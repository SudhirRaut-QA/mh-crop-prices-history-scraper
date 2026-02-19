from seleniumbase import SB
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

# --- CONFIG ---
# We use the exact MSAMB Option Values from the HTML you provided!
CROPS = [
    {"id": "onion", "name": "Onion", "marathi": "कांदा", "msamb_val": "08035"},
    {"id": "soyabean", "name": "Soybean", "marathi": "सोयाबीन", "msamb_val": "04017"},
    {"id": "cotton", "name": "Cotton", "marathi": "कापूस", "msamb_val": "01001"},
    {"id": "maize", "name": "Maize", "marathi": "मका", "msamb_val": "02015"},
    {"id": "wheat", "name": "Wheat", "marathi": "गहू", "msamb_val": "02009"},
    {"id": "arhar-turred-gram-whole", "name": "Tur", "marathi": "तूर", "msamb_val": "03020"},
    {"id": "bengal-gram-gram-whole", "name": "Harbara", "marathi": "हरभरा", "msamb_val": "03006"},
    {"id": "tomato", "name": "Tomato", "marathi": "टोमॅटो", "msamb_val": "08071"},
    {"id": "pomegranate", "name": "Pomegranate", "marathi": "डाळिंब", "msamb_val": "07007"},
    {"id": "garlic", "name": "Garlic", "marathi": "लसूण", "msamb_val": "08045"},
    {"id": "marigold-calcutta", "name": "Marigold", "marathi": "झेंडू", "msamb_val": "16009"},
    {"id": "rose-local", "name": "Rose", "marathi": "गुलाब", "msamb_val": "16003"},
    {"id": "silk-cocoonbh-double-hybr", "name": "Cocoon", "marathi": "रेशीम कोष", "msamb_val": ""} # Note: MSAMB doesn't list Silk Cocoon.
]

# We are only saving data for the markets we actually care about to keep the JSON small!
TARGET_MARKETS = [
    "अहिल्यानगर", "राहता", "राहुरी", "आळेफाटा", "संगमनेर", "लासलगाव", 
    "पुणे", "सोलापूर", "नागपूर", "मुंबई", "लातूर", "अकोला", "अमरावती", 
    "वाशिम", "हिंगणघाट", "यवतमाळ", "जळगाव", "जालना", "पिंपळगाव", 
    "नारायणगाव", "सांगोला", "पंढरपूर", "सटाणा", "बारामती", "तळेगाव", "सातारा", "कल्याण"
]

def clean_price(text):
    """Removes commas and spaces to return a clean integer."""
    try:
        return int(text.replace(',', '').strip())
    except ValueError:
        return 0

# --- THE SCRAPER ---
start_time = time.time()
final_data = {"crops": {}}

# Initialize SeleniumBase
with SB(uc=True, test=True, headless=True) as sb:
    print("🚀 Booting up MSAMB Scraper...")
    sb.open("https://www.msamb.com/ApmcDetail/APMCPriceInformation")
    
    # Wait for the main dropdown to appear on the screen
    sb.wait_for_element_visible("#drpCommodities", timeout=15)
    
    for crop in CROPS:
        print(f"\nProcessing {crop['marathi']}...")
        
        # Setup the basic JSON structure for this crop
        final_data["crops"][crop['id']] = {
            "marathi": crop['marathi'],
            "english": crop['name'],
            "local": {},
            "outstate": {} # MSAMB doesn't have outstate, but we leave the key for Activepieces
        }
        
        # If MSAMB doesn't track this crop (like Cocoon), skip it
        if not crop['msamb_val']:
            print("   ⚠️ Not tracked by MSAMB. Skipping.")
            continue
            
        try:
            # 1. Select the crop from the dropdown using its Value
            sb.select_option_by_value("#drpCommodities", crop['msamb_val'])
            
            # 2. Wait for the "Data is loading..." text to DISAPPEAR
            # MSAMB shows an element with ID "OdivCommodity" while loading.
            sb.wait_for_element_not_visible("#OdivCommodity", timeout=15)
            
            # 3. Give it 1 extra second just to ensure the HTML table has fully rendered
            sb.sleep(1) 
            
            # 4. Extract the HTML
            html = sb.get_page_source()
            soup = BeautifulSoup(html, "html.parser")
            
            # 5. Find the table body
            tbody = soup.find("tbody", id="tblCommodity")
            if not tbody:
                print("   ❌ No table found.")
                continue
                
            # 6. Loop through the rows
            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                
                # We only want rows that have 7 columns (Market, Variety, Unit, Arrival, Min, Max, Avg)
                if len(cols) == 7:
                    market_name = cols[0].text.strip()
                    variety = cols[1].text.strip()
                    avg_price_text = cols[6].text.strip()
                    
                    price = clean_price(avg_price_text)
                    
                    # Does this market exist in our Target list?
                    # Example: "पुणे- खडकी" -> We just check if "पुणे" is in the string.
                    for target in TARGET_MARKETS:
                        if target in market_name and price > 0:
                            # We use the CLEAN target name (e.g. "पुणे" instead of "पुणे- खडकी")
                            # We only save the FIRST occurrence we find, since the newest date is at the top!
                            if target not in final_data["crops"][crop['id']]["local"]:
                                final_data["crops"][crop['id']]["local"][target] = {
                                    "modal_price": price,
                                    "variety": variety
                                }
                                print(f"   ✅ {target}: ₹{price} ({variety})")
                            break # Move to next row
                            
        except Exception as e:
            print(f"   ❌ Error processing {crop['marathi']}: {e}")

# --- PERFORMANCE METRICS ---
end_time = time.time()
duration_seconds = round(end_time - start_time, 2)
minutes = int(duration_seconds // 60)
seconds = int(duration_seconds % 60)
duration_formatted = f"{minutes}m {seconds}s"

# --- SAVE LOGIC ---
now = datetime.now()
file_path = f"data/{now.year}/{now.strftime('%m')}/crop_prices_{now.strftime('%Y-%m-%d')}.json"
os.makedirs(os.path.dirname(file_path), exist_ok=True)

output = {
    "timestamp": now.isoformat(),
    "execution_time_seconds": duration_seconds,
    "execution_time_formatted": duration_formatted,
    "crops": final_data["crops"]
}

with open(file_path, "w", encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n⏱️ Scrape completed in {duration_formatted}!")
print(f"💾 Saved to {file_path}")