# 🌾 Shetkari Sahayata - Mandi Price Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![SeleniumBase](https://img.shields.io/badge/SeleniumBase-UC%20Mode-green.svg)
![GitHub Actions](https://img.shields.io/badge/Automated-GitHub%20Actions-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**A fully automated, serverless agricultural commodity price scraper and publishing system for Maharashtra farmers.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Automation](#-automated-publishing-pipeline)

</div>

---

## 📖 Overview

This repository serves as the **backend data engine** for the **Shetkari Sahayata** (शेतकरी सहाय्यता) Facebook page and Telegram channel. It is a 100% automated, serverless solution designed to:

- 🕷️ **Scrape** daily agricultural commodity prices (Mandi rates) from multiple sources
- 🛡️ **Bypass** Cloudflare bot-protection using advanced undetected Chrome techniques
- 💾 **Store** historical price data in JSON format (GitHub as database)
- 🤖 **Publish** daily market insights to 10,000+ farmers via social media
- 📊 **Track** price trends across 13 major crops and 40+ markets

The system provides **zero-cost infrastructure** by leveraging GitHub Actions for compute and GitHub repository for storage, while delivering real-time agricultural market intelligence to farming communities.

---

## ✨ Features

### 🎯 **Dual-Source Data Collection**
- **Primary Source (MSAMB)**: Rich, detailed data from Maharashtra State Agricultural Marketing Board
  - Min/Max/Modal prices
  - Daily arrivals (quantity)
  - Trade dates
  - Variety information
  - 25+ local Maharashtra markets
  
- **Secondary Source (CommodityOnline)**: National market benchmarks
  - Out-of-state comparative pricing
  - Major markets: Indore, Delhi, Bangalore, Surat, etc.
  - Fallback for crops not tracked by MSAMB

### 🌾 **Tracked Commodities**
| Crop | Marathi Name | Key Markets |
|------|--------------|-------------|
| Onion | कांदा | Lasalgaon, Pimpalgaon, Pune |
| Soybean | सोयाबीन | Latur, Washim, Akola |
| Cotton | कापूस | Hinganghat, Sangamner |
| Maize | मका | Ahmednagar, Pune |
| Wheat | गहू | Pune, Solapur |
| Tur (Arhar) | तूर | Latur, Osmanabad |
| Harbara (Chana) | हरभरा | Latur, Ahmednagar |
| Tomato | टोमॅटो | Pune, Nashik |
| Pomegranate | डाळिंब | Pune, Solapur |
| Garlic | लसूण | Lasalgaon, Pune |
| Marigold | झेंडू | Pune, Nashik |
| Rose | गुलाब | Pune, Nashik |
| Cocoon | रेशीम कोष | Ramanagara, Kolar |

### 🔧 **Technical Features**
- ✅ Cloudflare bypass using SeleniumBase UC mode
- ✅ Intelligent retry logic and error handling
- ✅ Structured JSON output with metadata
- ✅ Automatic date-based file organization
- ✅ Performance metrics tracking
- ✅ Headless browser execution for CI/CD
- ✅ No external database required (Git as database)

---

## 🏗️ Architecture

### **Waterfall Data Pipeline**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA COLLECTION LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  GitHub Actions Cron (5:30 AM & 5:30 PM IST)                            │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │  Python Scraper │                                                     │
│  │  (SeleniumBase) │                                                     │
│  └────┬───────┬────┘                                                     │
│       │       │                                                           │
│       │       └──────────────────┐                                       │
│       │                          │                                       │
│       ▼                          ▼                                       │
│  ┌─────────────┐          ┌────────────────┐                           │
│  │    MSAMB    │          │ CommodityOnline│                           │
│  │  (Primary)  │          │  (Fallback)    │                           │
│  └─────────────┘          └────────────────┘                           │
│       │                          │                                       │
│       └──────────┬───────────────┘                                       │
│                  ▼                                                       │
│         ┌─────────────────┐                                             │
│         │ Data Processing │                                             │
│         │   & Cleaning    │                                             │
│         └────────┬────────┘                                             │
│                  ▼                                                       │
│         ┌─────────────────┐                                             │
│         │   JSON Output   │                                             │
│         │  with Metadata  │                                             │
│         └────────┬────────┘                                             │
│                  ▼                                                       │
│         ┌─────────────────┐                                             │
│         │  Git Commit &   │                                             │
│         │      Push       │                                             │
│         └────────┬────────┘                                             │
│                  ▼                                                       │
└──────────────────┼──────────────────────────────────────────────────────┘
                   │
┌──────────────────┼──────────────────────────────────────────────────────┐
│                  ▼         STORAGE LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│              GitHub Repository (Database)                                │
│         data/YYYY/MM/crop_prices_YYYY-MM-DD.json                        │
│                                                                           │
│         Public Access: raw.githubusercontent.com                        │
│                                                                           │
└──────────────────┬──────────────────────────────────────────────────────┘
                   │
┌──────────────────┼──────────────────────────────────────────────────────┐
│                  ▼      PUBLISHING LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Activepieces Workflow (6:45 PM IST)                                    │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │  Fetch JSON     │──────► Wait 5 mins (safeguard)                     │
│  │  (Custom JS)    │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │  HTML + CSS     │                                                     │
│  │  Generation     │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │   HCTI API      │──────► PNG Infographic                             │
│  │ (Image Render)  │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │  Loop: Process  │                                                     │
│  │   Each Crop     │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                               │
│           ├──────► Google Sheets (Historical DB)                        │
│           │                                                               │
│           ▼                                                               │
│  ┌─────────────────┐                                                     │
│  │ Google Gemini   │──────► AI-Generated Marathi Post                   │
│  │   2.5 Flash     │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                               │
│           ├──────► Facebook Graph API (Post with Image)                 │
│           │                                                               │
│           ├──────► Generate Facebook Deep Link                          │
│           │                                                               │
│           └──────► Telegram Bot API (sendPhoto)                         │
│                                                                           │
└──────────────────┬──────────────────────────────────────────────────────┘
                   │
                   ▼
            10,000+ Farmers
```

### **Data Flow Summary**

1. **Scraping Layer** (Python + SeleniumBase)
   - Fetches HTML from MSAMB and CommodityOnline
   - Parses tables using BeautifulSoup
   - Cleans and normalizes price data
   - Handles pagination and dynamic content

2. **Storage Layer** (GitHub Repository)
   - Stores daily JSON snapshots in `/data/YYYY/MM/` structure
   - Git history provides complete audit trail
   - Public raw.githubusercontent.com URLs for API-like access

3. **Publishing Layer** (Activepieces + APIs)
   - Automated workflow triggered at 6:45 PM IST
   - Transforms JSON into visual infographics
   - AI-generated Marathi social media posts
   - Multi-platform distribution (Facebook + Telegram)

---

## 🚀 Installation

### **Prerequisites**
- Python 3.10 or higher
- Git
- Chrome/Chromium browser (for local testing)

### **Local Setup**

#### **Windows**
```powershell
# Clone the repository
git clone https://github.com/yourusername/Mandi-Scraper.git
cd Mandi-Scraper

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install ChromeDriver (SeleniumBase will auto-manage)
sbase install chromedriver

# Run the scraper
python scraper.py
```

#### **Linux/macOS**
```bash
# Clone the repository
git clone https://github.com/yourusername/Mandi-Scraper.git
cd Mandi-Scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install ChromeDriver
sbase install chromedriver

# Run the scraper
python scraper.py
```

---

## 💻 Usage

### **Manual Execution**

Run the scraper manually to fetch today's prices:

```bash
python scraper.py
```

**Output:**
```
🚀 Booting up MSAMB (Primary Engine)...

Processing कांदा from MSAMB...
   ✅ लासलगाव: Avg ₹2500 | Min ₹2200 | Max ₹2800 | Date: 19-02-2026
   ✅ पुणे: Avg ₹2600 | Min ₹2300 | Max ₹2900 | Date: 19-02-2026

🚀 Warming up CommodityOnline (National Fallback)...
   🌍 Checking National Markets for Onion...
      ✅ Indore: ₹2400
      ✅ Delhi: ₹2700

⏱️ Scrape completed in 2m 34s!
💾 Saved to data/2026/02/crop_prices_2026-02-19.json
```

### **Output Format**

The scraper generates a JSON file in the following structure:

```json
{
  "timestamp": "2026-02-19T12:30:45.123456",
  "execution_time_seconds": 154.23,
  "execution_time_formatted": "2m 34s",
  "crops": {
    "onion": {
      "marathi": "कांदा",
      "english": "Onion",
      "local": {
        "लासलगाव": {
          "modal_price": 2500,
          "min_price": 2200,
          "max_price": 2800,
          "arrival": 15000,
          "variety": "Red",
          "trade_date": "19-02-2026"
        }
      },
      "outstate": {
        "Indore": {
          "modal_price": 2400,
          "variety": "Nasik Red"
        }
      }
    }
  }
}
```

### **Accessing Raw JSON via URL**

Once committed to GitHub, the JSON file is publicly accessible:

```
https://raw.githubusercontent.com/yourusername/Mandi-Scraper/main/data/2026/02/crop_prices_2026-02-19.json
```

This URL is used by the Activepieces workflow to fetch and process data.

---

## 🤖 Automated Publishing Pipeline

### **GitHub Actions Workflow**

The scraper runs automatically twice daily using GitHub Actions:

- **Schedule**: `0 0,12 * * *` (12:00 AM & 12:00 PM UTC = 5:30 AM & 5:30 PM IST)
- **Trigger**: Can also be manually triggered via workflow_dispatch
- **Environment**: Ubuntu-latest with Python 3.10
- **Display**: Uses `xvfb-run` for headless browser execution

**Workflow File**: [`.github/workflows/daily_scrape.yml`](.github/workflows/daily_scrape.yml)

---

## 🎨 Activepieces Publishing Workflow

To ensure farmers receive timely updates without manual intervention, an **Activepieces** automation pipeline runs every evening at **6:45 PM IST**, processing and distributing the scraped data across multiple platforms.

### **🔄 Flow Architecture & Steps**

#### **Step 1: Start - Run Daily at 6:45 PM**
- **Trigger**: Cron job `45 18 * * *` (6:45 PM IST)
- **Purpose**: Scheduled automation to publish daily market insights

#### **Step 2: Fetch & Format Market Data**
- **Action**: Custom JavaScript code
- **Process**:
  - Fetches today's JSON file directly from `raw.githubusercontent.com` endpoint
  - Maps local Maharashtrian APMC data and out-of-state fallback data
  - Generates structured HTML rows with CSS styling
  - Creates data arrays for downstream processing

#### **Step 3: Wait 5 Minutes (Ensure Data is Fresh)**
- **Action**: Delay safeguard
- **Purpose**: Ensures GitHub Actions has fully committed and deployed the latest JSON file before processing

#### **Step 4: Create Infographic Image**
- **Service**: [HCTI (HTML/CSS to Image) API](https://htmlcsstoimage.com/)
- **Input**: Dynamically generated HTML + CSS
- **Output**: Visually appealing, easily readable market rate infographic (PNG)
- **Features**:
  - Crop-wise prices in tabular format
  - Min/Max/Modal rates with color coding
  - Arrival quantities
  - Trade dates
  - Responsive design optimized for mobile viewing

#### **Step 5: Loop - Process Each Crop**
- **Action**: Array iterator
- **Scope**: Iterates through the structured array of all tracked crops
- **Crops Processed**: Onion, Soybean, Cotton, Maize, Wheat, Tur, Harbara, Tomato, Pomegranate, Garlic, Marigold, Rose, Cocoon

#### **Step 6: Save Crop Rates to Database** (Inside Loop)
- **Service**: Google Sheets API
- **Data Fields Stored**:
  - Date
  - Trade Date
  - Min Price
  - Max Price
  - Average/Modal Price
  - Arrival Quantities
  - Generated Image URL
- **Purpose**: Future trend analysis, farmer queries, historical reports

#### **Step 7: AI - Write Marathi Social Media Post**
- **Service**: Google Gemini 2.5 Flash
- **Prompt Role**: Agricultural market expert
- **Process**:
  - Feeds raw JSON data to Gemini API
  - Uses strict prompt engineering
  - Analyzes day's highest prices and maximum arrivals
  - Writes unique, engaging, emoji-rich summary in natural Marathi
  - Optimized for social media virality and farmer engagement
- **Example Output**:
  ```
  🌾 आजचे मंडी भाव (19 फेब्रुवारी 2026)
  
  🧅 कांदा - लासलगाव मंडीत सर्वाधिक ₹2,800/क्विंटल! आवक 15 टन
  🌿 सोयाबीन - लातूर येथे ₹4,200/क्विंटल (उत्तम दर!)
  
  संपूर्ण माहिती खाली पहा 👇
  #MandiRates #शेतकरीसहाय्यता
  ```

#### **Step 8: Publish Post to Facebook**
- **Service**: Facebook Graph API
- **Platform**: Shetkari Sahayata Facebook Page
- **Content Posted**:
  - HCTI-generated infographic (image attachment)
  - Gemini-generated Marathi caption
  - Automatic hashtags and engagement triggers
- **Result**: Returns unique post ID for tracking

#### **Step 9: Generate Clickable Facebook Link**
- **Action**: Custom JavaScript parser
- **Process**:
  - Parses unique `[PAGE_ID]_[POST_ID]` returned by Facebook API
  - Constructs clean, deep-linked URL
  - Example: `https://www.facebook.com/ShetkariSahayata/posts/123456789`
- **Purpose**: Enable cross-platform sharing and drive organic engagement

#### **Step 10: Send Update to Telegram**
- **Service**: Telegram Bot API (`/sendPhoto`)
- **Platform**: Shetkari Sahayata Telegram Channel
- **Content**:
  - Sends the infographic image
  - Brief, punchy Marathi caption
  - Embeds Facebook deep-link under "Shetkari Sahayata" text (clickable)
- **Purpose**:
  - Cross-platform distribution
  - Drive traffic from Telegram to Facebook
  - Increase organic reach and community engagement
- **Result**: Instant notification delivered to 10,000+ subscribers

---

## 🛠️ Technologies Used

### **Scraping & Automation**
| Technology | Purpose |
|------------|---------|
| **[SeleniumBase](https://github.com/seleniumbase/SeleniumBase)** | Undetected Chrome automation, bypasses Cloudflare bot detection |
| **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** | HTML parsing and data extraction |
| **[GitHub Actions](https://github.com/features/actions)** | Serverless cron job execution (free tier) |
| **Python 3.10+** | Core scripting language |

### **Publishing Pipeline**
| Technology | Purpose |
|------------|---------|
| **[Activepieces](https://www.activepieces.com/)** | Visual workflow automation platform |
| **[HCTI API](https://htmlcsstoimage.com/)** | HTML/CSS to PNG image rendering |
| **[Google Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/)** | Native AI text generation & market analysis |
| **[Google Sheets API](https://developers.google.com/sheets/api)** | Historical data logging and trend analysis |
| **[Facebook Graph API](https://developers.facebook.com/docs/graph-api)** | Automated social media posting |
| **[Telegram Bot API](https://core.telegram.org/bots/api)** | Cross-platform message distribution |

### **Infrastructure**
| Component | Purpose |
|-----------|---------|
| **GitHub Repository** | Version control + storage (database) |
| **Ubuntu (GitHub Runners)** | Execution environment for scraper |
| **Xvfb (Virtual Display)** | Headless browser automation |
| **raw.githubusercontent.com** | Public JSON API endpoint |

---

## 📂 Project Structure

```
Mandi-Scraper/
├── .github/
│   └── workflows/
│       └── daily_scrape.yml       # GitHub Actions automation config
├── data/
│   └── YYYY/                      # Year-based organization
│       └── MM/                    # Month-based organization
│           └── crop_prices_YYYY-MM-DD.json  # Daily price snapshots
├── downloaded_files/              # Temporary browser downloads (ignored)
├── venv/                          # Python virtual environment (ignored)
├── .gitignore                     # Ignored files (venv, __pycache__, etc.)
├── README.md                      # This comprehensive documentation
├── requirements.txt               # Python dependencies
└── scraper.py                     # Main scraper script (200 lines)
```

---

## 📊 Data Coverage

### **Maharashtra Markets (27)**
अहिल्यानगर (Ahmednagar), राहता (Rahata), राहुरी (Rahuri), आळेफाटा (Alephata), संगमनेर (Sangamner), लासलगाव (Lasalgaon), पुणे (Pune), सोलापूर (Solapur), नागपूर (Nagpur), मुंबई (Mumbai), लातूर (Latur), अकोला (Akola), अमरावती (Amravati), वाशिम (Washim), हिंगणघाट (Hinganghat), यवतमाळ (Yavatmal), जळगाव (Jalgaon), जालना (Jalna), पिंपळगाव (Pimpalgaon), नारायणगाव (Narayangaon), सांगोला (Sangola), पंढरपूर (Pandharpur), सटाणा (Satana), बारामती (Baramati), तळेगाव (Talegaon), सातारा (Satara), कल्याण (Kalyan)

### **Out-of-State Markets (17)**
Indore (MP), Delhi, Bangalore (KA), Surat (GJ), Rajkot (GJ), Ujjain (MP), Neemuch (MP), Mandsaur (MP), Bhopal (MP), Kadi (GJ), Dahod (GJ), Gulbarga (KA), Kolar (KA), Ramanagara (KA), Davangere (KA), Kanpur (UP), Nizamabad (TG)

---

## 🔍 How It Works

### **Scraping Logic**

#### **Part 1: MSAMB (Primary Source)**
1. Opens MSAMB website using undetected Chrome
2. For each crop, selects commodity from dropdown
3. Waits for dynamic table to render
4. Parses table rows to extract:
   - Market name (Marathi)
   - Trade date
   - Variety
   - Min/Max/Average prices
   - Arrival quantity (in quintals)
5. Filters for target Maharashtra markets
6. Stores rich, detailed local market data

#### **Part 2: CommodityOnline (Fallback Source)**
1. Opens CommodityOnline national portal
2. Bypasses Cloudflare with 6-second delay
3. For each crop, navigates to dedicated price page
4. Scrapes national market table
5. Filters out Maharashtra markets (to avoid duplicates)
6. Extracts modal prices for out-of-state markets
7. Provides comparative pricing context

#### **Part 3: Data Processing & Storage**
1. Merges local and out-of-state data
2. Adds metadata (timestamp, execution time)
3. Organizes by year/month folder structure
4. Saves as pretty-printed JSON with UTF-8 encoding
5. Git commits and pushes to repository
6. Makes data publicly accessible via raw.githubusercontent.com

---

## 🤝 Contributing

Contributions are welcome! Here are some ways you can help:

- 🐛 **Report bugs**: Create an issue with detailed reproduction steps
- 💡 **Suggest features**: Propose new markets, crops, or data sources
- 🔧 **Submit PRs**: Code improvements, bug fixes, documentation
- 📖 **Improve docs**: Fix typos, add examples, translate content
- 🌍 **Localization**: Add support for more regional languages

### **Development Workflow**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes with clear commit messages
4. Test locally: `python scraper.py`
5. Ensure no errors: Check JSON output validity
6. Commit: `git commit -m "Add: your feature description"`
7. Push: `git push origin feature/your-feature-name`
8. Create a Pull Request with detailed description

### **Code Style Guidelines**
- Follow PEP 8 for Python code
- Add comments for complex logic
- Update README.md if adding new features
- Test with both sources (MSAMB & CommodityOnline)

---

## 🐛 Troubleshooting

### **Common Issues**

**Issue: Cloudflare blocks scraper**
```
Solution: Ensure SeleniumBase UC mode is enabled
- Check: sb = SB(uc=True, test=True, headless=True)
- Update: pip install --upgrade seleniumbase
```

**Issue: ChromeDriver not found**
```
Solution: Reinstall ChromeDriver
- Command: sbase install chromedriver
```

**Issue: Incomplete data in JSON**
```
Solution: Increase wait times for dynamic content
- Adjust sleep values in scraper.py (sb.sleep())
- Check network speed and website responsiveness
```

**Issue: GitHub Actions fails**
```
Solution: Check workflow logs
- Verify xvfb-run is working
- Ensure requirements.txt is up-to-date
- Check GitHub Actions quota limits
```

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

### **MIT License Summary**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

---

## 🙏 Acknowledgments

- **MSAMB**: Maharashtra State Agricultural Marketing Board for providing public market data
- **CommodityOnline**: National commodity price aggregation
- **Farmers of Maharashtra**: The inspiration and primary beneficiaries of this project
- **Shetkari Sahayata Community**: 10,000+ followers on Facebook and Telegram who rely on accurate market information
- **Open Source Community**: SeleniumBase, BeautifulSoup, and Python ecosystem contributors

---

## 📞 Contact & Support

### **Social Media**
- 📘 **Facebook**: [Shetkari Sahayata Page](https://www.facebook.com/ShetkariSahayata)
- 📱 **Telegram**: [@ShetkariSahayata](https://t.me/ShetkariSahayata)

### **Technical Support**
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/Mandi-Scraper/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/Mandi-Scraper/discussions)
- 📧 **Email**: contact@shetkari-sahayata.com

### **Documentation**
- 📖 **Wiki**: [GitHub Wiki](https://github.com/yourusername/Mandi-Scraper/wiki)
- 🎥 **Video Tutorial**: Coming soon
- 📄 **API Docs**: Access raw JSON via GitHub raw URLs

---

## 📈 Project Stats

- **Total Crops Tracked**: 13
- **Total Markets Covered**: 44 (27 MH + 17 Out-of-state)
- **Daily Executions**: 2 times (5:30 AM & 5:30 PM IST)
- **Data Points per Day**: ~200+ price records
- **Storage Cost**: $0 (GitHub repository)
- **Compute Cost**: $0 (GitHub Actions free tier)
- **Community Reach**: 10,000+ farmers
- **Languages**: Python, JavaScript (Activepieces), Marathi (Output)

---

## 🗺️ Roadmap

### **Planned Features**
- [ ] SMS alerts for price spikes/drops
- [ ] WhatsApp integration via Business API
- [ ] Historical price trend charts
- [ ] Price prediction using ML models
- [ ] Mobile app (React Native)
- [ ] Multi-language support (Hindi, Kannada, Gujarati)
- [ ] Weather data integration
- [ ] Crop advisory based on market trends

### **In Progress**
- [x] GitHub Actions automation
- [x] Activepieces publishing pipeline
- [x] Comprehensive documentation

### **Completed**
- [x] Dual-source scraping (MSAMB + CommodityOnline)
- [x] Cloudflare bypass
- [x] JSON data storage
- [x] Facebook + Telegram publishing
- [x] AI-generated Marathi posts

---

## ⭐ Star History

If this project helps you or your community, please consider giving it a ⭐ on GitHub!

---

<div align="center">

**Made with ❤️ for Maharashtra Farmers**

*Empowering 10,000+ farmers with real-time market intelligence*

---

**"कृषी हा अर्थव्यवस्थेचा कणा आहे"**  
*"Agriculture is the backbone of the economy"*

---

© 2026 Shetkari Sahayata | [Privacy Policy](#) | [Terms of Service](#)

</div>
