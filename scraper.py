from seleniumbase import SB
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime

# --- CONFIG ---
CROPS = [
    {"id": "onion", "name": "Onion", "marathi": "कांदा"},
    {"id": "soyabean", "name": "Soybean", "marathi": "सोयाबीन"},
    {"id": "cotton", "name": "Cotton", "marathi": "कापूस"},
    {"id": "maize", "name": "Maize", "marathi": "मका"},
    {"id": "wheat", "name": "Wheat", "marathi": "गहू"},
    {"id": "arhar-turred-gram-whole", "name": "Tur", "marathi": "तूर"},
    {"id": "bengal-gram-gram-whole", "name": "Harbara", "marathi": "हरभरा"},
    {"id": "tomato", "name": "Tomato", "marathi": "टोमॅटो"},
    {"id": "pomegranate", "name": "Pomegranate", "marathi": "डाळिंब"},
    {"id": "garlic", "name": "Garlic", "marathi": "लसूण"},
    {"id": "marigold-calcutta", "name": "Marigold", "marathi": "झेंडू"},
    {"id": "rose-local", "name": "Rose", "marathi": "गुलाब"},
    {"id": "silk-cocoonbh-double-hybr", "name": "Cocoon", "marathi": "रेशीम कोष"}
]

# Upgraded based on your Agricultural Research
LOCAL_MARKETS = [
    # Static Columns
    "ahmednagar", "rahata", "rahuri", "junnar-alephata", "sangamner",
    # The New "Pramukh" Benchmarks
    "lasalgaon", "pune", "solapur", "nagpur", "mumbai", "latur", "akola",
    "amravati", "washim", "hinganghat", "yavatmal", "jalgaon", "jalna",
    "pimpalgaon", "narayangaon", "sangola", "pandharpur", "satana",
    "baramati", "talegaon", "satara"
]

OUTSTATE_MARKETS = [
    "Indore", "Delhi", "Bangalore", "Surat", "Rajkot", "Ujjain", "Neemuch",
    "Mandsaur", "Bhopal", "Kadi", "Dahod", "Gulbarga", "Kolar", "Ramanagara",
    "Davangere", "Kanpur", "Nizamabad"
]

def extract_price(text):
    match = re.search(r'([\d,]+)', text)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0

# --- THE SCRAPER ---
start_time = time.time()

with SB(uc=True, test=True, headless=True) as sb:
    final_data = {"crops": {}}
    
    print("🚀 Warming up browser to generate Cloudflare Cookie...")
    sb.open("https://www.commodityonline.com/")
    sb.sleep(6) 
    
    for crop in CROPS:
        print(f"\nProcessing {crop['name']}...")
        final_data["crops"][crop['id']] = {
            "marathi": crop['marathi'],
            "english": crop['name'],
            "local": {},
            "outstate": {}
        }

        # 1. LOCAL MARKETS
        for market_slug in LOCAL_MARKETS:
            url = f"https://www.commodityonline.com/mandiprices/{crop['id']}/maharashtra/{market_slug}"
            try:
                sb.open(url)
                
                soup = BeautifulSoup(sb.get_page_source(), "html.parser")
                rows = soup.select("table tbody tr")
                
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 9: 
                        market_in_table = cols[5].get_text(strip=True).lower()
                        search_name = market_slug.replace('junnar-', '').lower()
                        
                        if search_name in market_in_table:
                            variety = cols[2].get_text(strip=True)
                            price = extract_price(cols[8].get_text(strip=True))
                            
                            if price > 0:
                                clean_market_name = market_slug.replace('junnar-', '').capitalize()
                                final_data["crops"][crop['id']]["local"][clean_market_name] = {
                                    "modal_price": price, 
                                    "variety": variety
                                }
                                print(f"   ✅ {clean_market_name}: ₹{price}")
                                break 
            except Exception as e:
                pass
            
        # 2. OUTSTATE MARKETS
        print(f"   🌍 Checking Outstate...")
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
                            price = extract_price(cols[8].get_text(strip=True))
                            
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