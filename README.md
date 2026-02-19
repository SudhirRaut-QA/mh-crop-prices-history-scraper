# 🌾 Shetkari Sahayata - Mandi Price Scraper

## Overview
This repository serves as the backend data engine for the **Shetkari Sahayata** Facebook page and Telegram channel. It is a 100% automated, serverless web scraper designed to bypass Cloudflare and extract daily agricultural commodity prices (Mandi rates) for farmers in Maharashtra.

## 🏗️ Architecture
This project uses a "Waterfall Data Pipeline" to ensure maximum reliability and zero hosting costs:
1. **Scraper Engine:** Python with `SeleniumBase` (UC Mode) to natively bypass Cloudflare bot-protection.
2. **Automation:** GitHub Actions runs the scraper twice daily (5:30 AM & 5:30 PM IST).
3. **Database:** The extracted data is saved as a static JSON file directly into this repository (`/data/YYYY/MM/...`).
4. **Frontend Orchestration:** **Activepieces** reads the Raw GitHub JSON file daily at 6:00 PM, formats the data into an HTML table, renders an infographic via HCTI, and automatically posts to Facebook and Telegram.

## 🎯 Target Markets (Dynamic Routing)
The scraper prioritizes highly-searched benchmark markets for specific crops:
* **Onion:** Lasalgaon, Pimpalgaon, Pune
* **Soyabean:** Latur, Washim, Akola
* **Cotton:** Hinganghat, Sangamner
* **Outstate Benchmarks:** Indore (MP), Surat (GJ), Bangalore (KA)

## 📂 File Structure
* `scraper.py` - The core SeleniumBase extraction script.
* `.github/workflows/daily_scrape.yml` - The GitHub Actions cron job configuration.
* `requirements.txt` - Python dependencies (`seleniumbase`, `beautifulsoup4`).
* `/data/` - The historical archive of daily JSON price reports.

## 🚀 Local Testing
To run this scraper locally on Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
sbase install chromedriver
python scraper.py