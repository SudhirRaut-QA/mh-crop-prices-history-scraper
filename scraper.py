from seleniumbase import SB
from bs4 import BeautifulSoup
import json
import os
import time
import re
from datetime import datetime

# --- CONFIG ---
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
    {"id": "silk-cocoonbh-double-hybr", "name": "Cocoon", "marathi": "रेशीम कोष", "msamb_val": ""}
]

# Marathi Names for MSAMB
LOCAL_MARKETS = [
    "अहिल्यानगर", "राहता", "राहुरी", "आळेफाटा", "संगमनेर", "लासलगाव", 
    "पुणे", "सोलापूर", "नागपूर", "मुंबई", "लातूर", "अकोला", "अमरावती", 
    "वाशिम", "हिंगणघाट", "यवतमाळ", "जळगाव", "जालना", "पिंपळगाव", 
    "नारायणगाव", "सांगोला", "पंढरपूर", "सटाणा", "बारामती", "तळेगाव", "सातारा", "कल्याण"
]

# English Names for CommodityOnline
OUTSTATE_MARKETS = [
    "Indore", "Delhi", "Bangalore", "Surat", "Rajkot", "Ujjain", "Neemuch",
    "Mandsaur", "Bhopal", "Kadi", "Dahod", "Gulbarga", "Kolar", "Ramanagara",
    "Davangere", "Kanpur", "Nizamabad"
]

def clean_price(text):
    try:
        return int(text.replace(',', '').strip())
    except ValueError:
        return 0
        
def extract_co_price(text):
    match = re.search(r'([\d,]+)', text)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0

# --- THE SCRAPER ---
start_time = time.time()
final_data = {"crops": {}}

with SB(uc=True, test=True, headless=True) as sb:
    
    # ---------------------------------------------------------
    # PART 1: MSAMB FOR ENRICHED LOCAL MAHARASHTRA DATA
    # ---------------------------------------------------------
    print("🚀 Booting up MSAMB (Primary Engine)...")
    sb.open("https://www.msamb.com/ApmcDetail/APMCPriceInformation")
    sb.wait_for_element_visible("#drpCommodities", timeout=15)
    
    for crop in CROPS:
        print(f"\nProcessing {crop['marathi']} from MSAMB...")
        final_data["crops"][crop['id']] = {
            "marathi": crop['marathi'],
            "english": crop['name'],
            "local": {},
            "outstate": {}
        }
        
        if not crop['msamb_val']:
            print("   ⚠️ Not tracked by MSAMB. Skipping to National Fallback.")
            continue
            
        try:
            sb.select_option_by_value("#drpCommodities", crop['msamb_val'])
            sb.wait_for_element_not_visible("#OdivCommodity", timeout=15)
            sb.sleep(1.5) # Extra buffer for table rendering
            
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            tbody = soup.find("tbody", id="tblCommodity")
            if not tbody:
                continue
                
            current_trade_date = "N/A"
            rows = tbody.find_all("tr")
            
            for row in rows:
                cols = row.find_all("td")
                
                # Check for Date Row
                if len(cols) == 1 and cols[0].has_attr('colspan'):
                    current_trade_date = cols[0].text.strip()
                    continue 
                
                # Check for Data Row
                if len(cols) == 7:
                    market_name = cols[0].text.strip()
                    variety = cols[1].text.strip()
                    
                    arrival = clean_price(cols[3].text.strip())
                    min_p = clean_price(cols[4].text.strip())
                    max_p = clean_price(cols[5].text.strip())
                    avg_p = clean_price(cols[6].text.strip())
                    
                    for target in LOCAL_MARKETS:
                        if target in market_name and avg_p > 0:
                            if target not in final_data["crops"][crop['id']]["local"]:
                                final_data["crops"][crop['id']]["local"][target] = {
                                    "modal_price": avg_p,
                                    "min_price": min_p,
                                    "max_price": max_p,
                                    "arrival": arrival,
                                    "variety": variety,
                                    "trade_date": current_trade_date
                                }
                                print(f"   ✅ {target}: Avg ₹{avg_p} | Min ₹{min_p} | Max ₹{max_p} | Date: {current_trade_date}")
                            break 
        except Exception as e:
            print(f"   ❌ Error extracting {crop['marathi']}: {e}")

    # ---------------------------------------------------------
    # PART 2: COMMODITY ONLINE FOR OUT-OF-STATE DATA
    # ---------------------------------------------------------
    print("\n🚀 Warming up CommodityOnline (National Fallback)...")
    sb.open("https://www.commodityonline.com/")
    sb.sleep(6) # Cloudflare bypass
    
    for crop in CROPS:
        print(f"   🌍 Checking National Markets for {crop['name']}...")
        try:
            sb.open(f"https://www.commodityonline.com/mandiprices/{crop['id']}")
            sb.sleep(1)
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            rows = soup.select("table tbody tr")
            
            found_outstate = set()
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 9:
                    market_col = cols[5].get_text(strip=True).lower()
                    state_col = cols[3].get_text(strip=True).lower()
                    
                    if "maharashtra" in state_col:
                        continue 
                        
                    for out_mkt in OUTSTATE_MARKETS:
                        if out_mkt.lower() in market_col and out_mkt not in found_outstate:
                            variety = cols[2].get_text(strip=True)
                            price = extract_co_price(cols[8].get_text(strip=True))
                            
                            if price > 0:
                                final_data["crops"][crop['id']]["outstate"][out_mkt] = {
                                    "modal_price": price,
                                    "variety": variety
                                }
                                found_outstate.add(out_mkt)
                                print(f"      ✅ {out_mkt}: ₹{price}")
        except Exception as e:
            pass

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