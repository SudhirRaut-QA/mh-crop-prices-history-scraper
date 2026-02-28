#!/usr/bin/env python3
"""
Shetkari Sahayata - Agricultural Mandi Price Scraper
======================================================

A fully automated web scraper that collects daily agricultural commodity prices
from multiple sources and stores them in structured JSON format.

Data Sources:
-------------
1. MSAMB (Maharashtra State Agricultural Marketing Board)
   - Primary source for local Maharashtra markets
   - Provides: Min/Max/Modal prices, arrivals, trade dates, variety info
   
2. CommodityOnline (National Portal)
   - Fallback source for out-of-state market benchmarks
   - Provides: Modal prices for major Indian markets

Output:
-------
Daily JSON file: data/YYYY/MM/crop_prices_YYYY-MM-DD.json

Structure:
{
  "timestamp": "ISO 8601 timestamp",
  "execution_time_seconds": float,
  "execution_time_formatted": "Xm Ys",
  "crops": {
    "crop_id": {
      "marathi": "मराठी नाव",
      "english": "English Name",
      "local": {"market": {prices, arrival, variety, trade_date}},
      "outstate": {"market": {modal_price, variety}}
    }
  }
}

Usage:
------
    python scraper.py

Requirements:
-------------
    - Python 3.10+
    - seleniumbase
    - beautifulsoup4
    - Chrome/Chromium browser

Author: Shetkari Sahayata Team
License: MIT
Repository: https://github.com/yourusername/Mandi-Scraper
"""

import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from seleniumbase import SB
from bs4 import BeautifulSoup


# =============================================================================
# CONFIGURATION
# =============================================================================

# Crops to track with their identifiers across different platforms
CROPS = [
    {"id": "onion", "name": "Onion", "marathi": "कांदा", "msamb_val": "08035", "commodityonline_id": "onion"},
    {"id": "soyabean", "name": "Soybean", "marathi": "सोयाबीन", "msamb_val": "04017", "commodityonline_id": "soyabean"},
    {"id": "cotton", "name": "Cotton", "marathi": "कापूस", "msamb_val": "01001", "commodityonline_id": "cotton"},
    {"id": "maize", "name": "Maize", "marathi": "मका", "msamb_val": "02015", "commodityonline_id": "maize"},
    {"id": "wheat", "name": "Wheat", "marathi": "गहू", "msamb_val": "02009", "commodityonline_id": "wheat"},
    {"id": "arhar-turred-gram-whole", "name": "Tur", "marathi": "तूर", "msamb_val": "03020", "commodityonline_id": "arhar-turred-gram-whole"},
    {"id": "bengal-gram-gram-whole", "name": "Harbara", "marathi": "हरभरा", "msamb_val": "03006", "commodityonline_id": "bengal-gram-gram-whole"},
    {"id": "tomato", "name": "Tomato", "marathi": "टोमॅटो", "msamb_val": "08071", "commodityonline_id": "tomato"},
    {"id": "pomegranate", "name": "Pomegranate", "marathi": "डाळिंब", "msamb_val": "07007", "commodityonline_id": "pomegranate"},
    {"id": "garlic", "name": "Garlic", "marathi": "लसूण", "msamb_val": "08045", "commodityonline_id": "garlic"},
    {"id": "marigold-calcutta", "name": "Marigold", "marathi": "झेंडू", "msamb_val": "16009", "commodityonline_id": "marigold-calcutta"},
    {"id": "rose-local", "name": "Rose", "marathi": "गुलाब", "msamb_val": "16003", "commodityonline_id": "rose-local"},
    {"id": "green-chilli", "name": "Green Chilli", "marathi": "हिरवी मिरची", "msamb_val": "10013", "commodityonline_id": "green-chilli"},
    {"id": "silk-cocoonbh-double-hybr", "name": "Cocoon", "marathi": "रेशीम कोष", "msamb_val": "", "commodityonline_id": "silk-cocoonbh-double-hybr"}  # Not on MSAMB
]

# Target Maharashtra markets (in Marathi) to extract from MSAMB
# These are high-priority APMCs with significant trading volumes
LOCAL_MARKETS: List[str] = [
    "अहिल्यानगर", "राहता", "राहुरी", "आळेफाटा", "संगमनेर", "लासलगाव", 
    "पुणे", "सोलापूर", "नागपूर", "मुंबई", "लातूर", "अकोला", "अमरावती", 
    "वाशिम", "हिंगणघाट", "यवतमाळ", "जळगाव", "जालना", "पिंपळगाव", 
    "नारायणगाव", "सांगोला", "पंढरपूर", "सटाणा", "बारामती", "तळेगाव", "सातारा", "कल्याण"
]

# Out-of-state benchmark markets (in English) to extract from CommodityOnline
# These provide comparative pricing context for farmers
# Note: We collect ALL non-Maharashtra markets, not just specific ones
MAHARASHTRA_VARIATIONS: List[str] = [
    "maharashtra", "maharastra", "mh"
]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clean_price(text: str) -> int:
    """
    Clean and convert price string to integer.
    
    Removes commas and whitespace, then converts to integer.
    Returns 0 if conversion fails (handles missing/invalid data gracefully).
    
    Args:
        text (str): Raw price string from scraped data (e.g., "2,500", "1500 ")
    
    Returns:
        int: Cleaned price as integer, or 0 if invalid
    
    Examples:
        >>> clean_price("2,500")
        2500
        >>> clean_price("N/A")
        0
    """
    try:
        return int(text.replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0


def extract_co_price(text: str) -> int:
    """
    Extract numeric price from CommodityOnline text.
    
    Uses regex to find first sequence of digits (with optional commas),
    then cleans and converts to integer.
    
    Args:
        text (str): Raw price cell text from CommodityOnline (may contain symbols/text)
    
    Returns:
        int: Extracted price as integer, or 0 if no match found
    
    Examples:
        >>> extract_co_price("₹ 2,500")
        2500
        >>> extract_co_price("Price: 1500 per quintal")
        1500
    """
    match = re.search(r'([\d,]+)', text)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0


# =============================================================================
# MAIN SCRAPING LOGIC
# =============================================================================

# Initialize performance tracking
start_time: float = time.time()

# Initialize output data structure
final_data: Dict[str, Any] = {"crops": {}}

# Create SeleniumBase instance with undetected-chromedriver mode
# uc=True: Bypasses Cloudflare bot detection
# test=True: Enables pytest mode for better error handling
# headless=True: Runs browser without GUI (required for CI/CD)
with SB(uc=True, test=True, headless=True) as sb:
    
    # =========================================================================
    # PART 1: MSAMB (MAHARASHTRA STATE AGRICULTURAL MARKETING BOARD)
    # =========================================================================
    # Primary data source providing rich market intelligence:
    # - Min/Max/Modal prices for local Maharashtra APMCs
    # - Daily arrival quantities (in quintals)
    # - Trade dates and commodity varieties
    # - Market-specific data for 27+ Maharashtra mandis
    
    print("🚀 Booting up MSAMB (Primary Engine)...")
    sb.open("https://www.msamb.com/ApmcDetail/APMCPriceInformation")
    
    # Wait for commodity dropdown to be interactive
    sb.wait_for_element_visible("#drpCommodities", timeout=15)
    
    # Iterate through all configured crops
    for crop in CROPS:
        print(f"\nProcessing {crop['marathi']} from MSAMB...")
        
        # Initialize crop data structure
        final_data["crops"][crop['id']] = {
            "marathi": crop['marathi'],
            "english": crop['name'],
            "local": {},      # Maharashtra markets (from MSAMB)
            "outstate": {}    # Out-of-state markets (from CommodityOnline)
        }
        
        # Skip if crop not tracked by MSAMB (e.g., Cocoon)
        if not crop['msamb_val']:
            print("   ⚠️ Not tracked by MSAMB. Skipping to National Fallback.")
            continue
            
        try:
            # Select crop from dropdown menu
            sb.select_option_by_value("#drpCommodities", crop['msamb_val'])
            
            # Wait for loading overlay to disappear
            sb.wait_for_element_not_visible("#OdivCommodity", timeout=15)
            
            # Extra buffer to ensure dynamic table is fully rendered
            sb.sleep(1.5)
            
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            tbody = soup.find("tbody", id="tblCommodity")
            if not tbody:
                continue
                
            current_trade_date = "N/A"
            rows = tbody.find_all("tr")
            
            # Parse table rows (mix of date headers and data rows)
            for row in rows:
                cols = row.find_all("td")
                
                # Date Row: Single column with colspan attribute
                # Format: "Trade Date: DD-MM-YYYY"
                if len(cols) == 1 and cols[0].has_attr('colspan'):
                    current_trade_date = cols[0].text.strip()
                    continue
                
                # Data Row: 7 columns with market details
                # Columns: [Market, Variety, Grade, Arrival, Min, Max, Modal]
                if len(cols) == 7:
                    # Extract market information
                    market_name: str = cols[0].text.strip()
                    variety: str = cols[1].text.strip()
                    
                    # Extract and clean price/arrival data
                    arrival: int = clean_price(cols[3].text.strip())  # Quintals
                    min_p: int = clean_price(cols[4].text.strip())    # ₹/Quintal
                    max_p: int = clean_price(cols[5].text.strip())    # ₹/Quintal
                    avg_p: int = clean_price(cols[6].text.strip())    # ₹/Quintal (Modal)
                    
                    # Check if this row matches any of our target markets
                    for target in LOCAL_MARKETS:
                        if target in market_name and avg_p > 0:
                            # Store first match only (avoid duplicates from sub-markets)
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
                            break  # Move to next row once match found
        
        except Exception as e:
            # Log error but continue with other crops
            print(f"   ❌ Error extracting {crop['marathi']}: {e}")

    # =========================================================================
    # PART 2: COMMODITYONLINE (FALLBACK + OUTSTATE)
    # =========================================================================
    # Secondary data source with priority-based strategy:
    # 1. FALLBACK: Fill missing Maharashtra markets from MSAMB
    # 2. OUTSTATE: Collect all out-of-state benchmark markets
    # 3. NO MSAMB CROPS: Get all available markets (like Cocoon)
    
    print("\n🚀 Warming up CommodityOnline (Fallback Engine)...")
    sb.open("https://www.commodityonline.com/")
    
    # Cloudflare bot detection bypass - allow time for page verification
    sb.sleep(6)
    
    # Market name normalization mapping (CommodityOnline English → MSAMB Marathi)
    market_name_map: Dict[str, str] = {
        "ahilyanagar": "अहिल्यानगर",
        "nashik": "नाशिक", 
        "sangamner": "संगमनेर",
        "lasalgaon": "लासलगाव",
        "pune": "पुणे",
        "solapur": "सोलापूर",
        "nagpur": "नागपूर",
        "mumbai": "मुंबई",
        "latur": "लातूर",
        "akola": "अकोला",
        "amravati": "अमरावती",
        "washim": "वाशिम",
        "hinganghat": "हिंगणघाट",
        "yavatmal": "यवतमाळ",
        "jalgaon": "जळगाव",
        "jalna": "जालना",
        "pimpalgaon": "पिंपळगाव",
        "narayangaon": "नारायणगाव",
        "sangola": "सांगोला",
        "pandharpur": "पंढरपूर",
        "satana": "सटाणा",
        "baramati": "बारामती",
        "talegaon": "तळेगाव",
        "satara": "सातारा",
        "kalyan": "कल्याण",
        "rahata": "राहता",
        "rahuri": "राहुरी",
        "alephata": "आळेफाटा"
    }
    
    # Iterate through crops to fetch national market data
    for crop in CROPS:
        print(f"\n   🌍 Checking CommodityOnline for {crop['name']}...")
        
        # Determine which LOCAL_MARKETS are missing from MSAMB
        missing_local_markets = []
        if crop['msamb_val']:
            # For crops with MSAMB, find which markets we didn't get
            found_local = set(final_data["crops"][crop['id']]["local"].keys())
            missing_local_markets = [m for m in LOCAL_MARKETS if m not in found_local]
            if missing_local_markets:
                print(f"      🔍 Looking for {len(missing_local_markets)} missing MH markets...")
        
        try:
            # Use commodityonline_id if available, otherwise fall back to regular id
            co_id = crop.get('commodityonline_id', crop['id'])
            url = f"https://www.commodityonline.com/mandiprices/{co_id}"
            
            # Navigate to crop-specific price page
            print(f"      🔗 Visiting: {url}")
            sb.open(url)
            sb.sleep(1)  # Brief pause for page load
            
            # Parse price table
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            rows = soup.select("table tbody tr")
            
            if not rows:
                print(f"      ⚠️ No price table found (page might not have data for this crop)")
                continue
            
            print(f"      📋 Found {len(rows)} price rows to process")
            
            # Track processed markets to avoid duplicates
            processed_markets: set = set()
            outstate_found: int = 0
            local_fallback_found: int = 0
            total_rows_checked: int = 0
            
            for row in rows:
                total_rows_checked += 1
                cols = row.find_all("td")
                
                # Table structure: [Commodity, ArrivalDate, Variety, State, District, Market, MinPrice, MaxPrice, AvgPrice, ...]
                if len(cols) >= 9:
                    # Extract market information
                    state: str = cols[3].get_text(strip=True)
                    market_name: str = cols[5].get_text(strip=True)
                    variety: str = cols[2].get_text(strip=True)
                    price: int = extract_co_price(cols[8].get_text(strip=True))
                    
                    # Skip if no valid price or already processed
                    if price <= 0 or market_name in processed_markets:
                        continue
                    
                    # Normalize names for matching
                    market_lower = market_name.lower()
                    state_lower = state.lower()
                    market_normalized = market_lower.replace(" ", "").replace("-", "")
                    
                    # ===== CASE 1: CROPS WITHOUT MSAMB DATA (e.g., Cocoon) =====
                    # Get ALL available markets since MSAMB doesn't track this crop
                    if not crop['msamb_val']:
                        processed_markets.add(market_name)
                        if "maharashtra" in state_lower:
                            # Translate English market name to Marathi
                            marathi_name = market_name  # Default to English if translation not found
                            for eng_key, mar_val in market_name_map.items():
                                if eng_key in market_normalized:
                                    marathi_name = mar_val
                                    break
                            
                            final_data["crops"][crop['id']]["local"][marathi_name] = {
                                "modal_price": price,
                                "variety": variety
                            }
                            local_fallback_found += 1
                            print(f"      ✅ {marathi_name} (MH): ₹{price}")
                        else:
                            final_data["crops"][crop['id']]["outstate"][market_name] = {
                                "modal_price": price,
                                "variety": variety
                            }
                            outstate_found += 1
                            print(f"      ✅ {market_name}: ₹{price}")
                        continue
                    
                    # ===== CASE 2: MAHARASHTRA FALLBACK (for MSAMB crops) =====
                    # Check if this Maharashtra market was missing from MSAMB
                    if "maharashtra" in state_lower and missing_local_markets:
                        # Try to match with missing markets
                        matched_market = None
                        for missing_market in missing_local_markets:
                            # Check direct mapping
                            for eng_key, mar_val in market_name_map.items():
                                if eng_key in market_normalized and mar_val == missing_market:
                                    matched_market = missing_market
                                    break
                            
                            if matched_market:
                                break
                        
                        if matched_market:
                            final_data["crops"][crop['id']]["local"][matched_market] = {
                                "modal_price": price,
                                "variety": variety
                            }
                            missing_local_markets.remove(matched_market)
                            processed_markets.add(market_name)
                            local_fallback_found += 1
                            print(f"      ✅ {matched_market} (Fallback): ₹{price}")
                        continue
                    
                    # ===== CASE 3: OUTSTATE MARKETS (for all crops) =====
                    # Collect ALL non-Maharashtra markets for price comparison
                    # Skip Maharashtra since it's already handled in CASE 1 & 2
                    is_maharashtra = any(mh_var in state_lower for mh_var in MAHARASHTRA_VARIATIONS)
                    if is_maharashtra:
                        continue
                    
                    # Add this outstate market (use actual market name from the page)
                    final_data["crops"][crop['id']]["outstate"][market_name] = {
                        "modal_price": price,
                        "variety": variety
                    }
                    processed_markets.add(market_name)
                    outstate_found += 1
                    print(f"      ✅ {market_name} ({state}): ₹{price}")
            
            # Summary for this crop
            if total_rows_checked > 0:
                print(f"      📊 Processed {total_rows_checked} rows → Found: {local_fallback_found} local fallback, {outstate_found} outstate")
                if outstate_found == 0 and not crop.get('msamb_val'):
                    print(f"      ⚠️ No outstate markets found despite checking {total_rows_checked} rows")
        
        except Exception as e:
            # Log error but continue with other crops
            print(f"      ❌ Error: {e}")

# =============================================================================
# PERFORMANCE METRICS & OUTPUT
# =============================================================================

# Calculate execution time
end_time: float = time.time()
duration_seconds: float = round(end_time - start_time, 2)
minutes: int = int(duration_seconds // 60)
seconds: int = int(duration_seconds % 60)
duration_formatted: str = f"{minutes}m {seconds}s"

# Generate output file path with date-based organization
now: datetime = datetime.now()
file_path: str = f"data/{now.year}/{now.strftime('%m')}/crop_prices_{now.strftime('%Y-%m-%d')}.json"

# Create directory structure if it doesn't exist
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Construct final output with metadata
output: Dict[str, Any] = {
    "timestamp": now.isoformat(),
    "execution_time_seconds": duration_seconds,
    "execution_time_formatted": duration_formatted,
    "crops": final_data["crops"]
}

# Write JSON file with UTF-8 encoding (supports Marathi characters)
# indent=2: Pretty-print for readability
# ensure_ascii=False: Preserve Marathi Unicode characters
with open(file_path, "w", encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Print completion summary
print(f"\n⏱️ Scrape completed in {duration_formatted}!")
print(f"💾 Saved to {file_path}")
print(f"\n📊 Summary:")
print(f"   Total crops processed: {len(CROPS)}")
print(f"   Crops with local data: {sum(1 for c in final_data['crops'].values() if c['local'])}")
print(f"   Crops with outstate data: {sum(1 for c in final_data['crops'].values() if c['outstate'])}")

# Detailed breakdown
total_local = sum(len(c['local']) for c in final_data['crops'].values())
total_outstate = sum(len(c['outstate']) for c in final_data['crops'].values())
print(f"\n📈 Data Points Collected:")
print(f"   Local markets: {total_local} entries")
print(f"   Outstate markets: {total_outstate} entries")
print(f"   Total: {total_local + total_outstate} market entries")