# 🚀 Muraena.ai Local Scraper - Open Source Edition

**No Apify. No costs. Full control. Pure open source!**

This is a complete rewrite using Playwright to scrape Muraena.ai directly from your local machine. All the power, none of the hassle!

---

## ✨ Features

### Core Features
- ✅ **100% Local** - Runs on your machine, no cloud services
- ✅ **No Costs** - Completely free, open source
- ✅ **Fast** - Direct browser automation, no API delays
- ✅ **Multi-Page** - Scrape hundreds of pages automatically
- ✅ **Smart Reveal** - Automatically clicks "Reveal" buttons for hidden data
- ✅ **Multiple Exports** - JSON, CSV, and Excel formats
- ✅ **Deduplication** - Automatically removes duplicate entries
- ✅ **Screenshots** - Saves debugging screenshots automatically

### Two Versions

| File | Description | Use Case |
|------|-------------|----------|
| `muraena_scraper_local.py` | Single-page scraper | Quick testing, single page |
| `muraena_scraper_multipage.py` | Multi-page scraper | Bulk scraping, production use |

---

## 📦 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements_local.txt
```

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

That's it! No Apify account, no API tokens needed!

---

## ⚙️ Configuration

### 1. Copy the Environment File

```bash
cp .env.local .env
```

### 2. Edit `.env` with Your Target URL

```dotenv
# Your search URL with filters
TARGET_URL=https://app.muraena.ai/companies_search/results?company_countries[]=United%20States&industries[]=Commercial%20Real%20Estate&page=7&size=100

# For multi-page scraping
BASE_URL=https://app.muraena.ai/companies_search/results?company_countries[]=United%20States&industries[]=Commercial%20Real%20Estate

# Settings
HEADLESS=false  # Set 'true' to run without visible browser
PAGE_SIZE=100   # Results per page (max 100)
```

### 3. Update Your Cookies

Open either scraper file and update the `COOKIES` list with your cookies from EditThisCookie:

```python
COOKIES = [
    {
        "name": "_ga",
        "value": "YOUR_VALUE_HERE",
        # ... etc
    },
    # ... more cookies
]
```

**You already have these cookies!** Just copy them from your earlier EditThisCookie export.

---

## 🚀 Usage

### Single Page Scraping (Quick Test)

```bash
python muraena_scraper_local.py
```

**What it does:**
- Scrapes one page (the TARGET_URL)
- Clicks all reveal buttons
- Exports to JSON + CSV
- Saves screenshots to `screenshots/` folder

### Multi-Page Scraping (Bulk Data)

```bash
# Scrape pages 1-10
python muraena_scraper_multipage.py --start-page 1 --end-page 10

# Scrape first 5 pages
python muraena_scraper_multipage.py --pages 5

# Scrape pages 7-15
python muraena_scraper_multipage.py --start-page 7 --end-page 15
```

**What it does:**
- Scrapes multiple pages automatically
- Deduplicates entries across pages
- Progress tracking
- Exports to JSON + CSV + Excel
- Handles pagination automatically

---

## 📊 Output Files

### File Naming

```
muraena_results_20241211_143052.json
muraena_results_20241211_143052.csv
muraena_multipage_20241211_143052.xlsx
```

### JSON Format

```json
[
  {
    "companyName": {
      "text": "Acme Real Estate Corp",
      "link": "https://..."
    },
    "email": {
      "text": "contact@acmerealestate.com",
      "link": ""
    },
    "phone": {
      "text": "+1-555-0100",
      "link": ""
    },
    "industry": {
      "text": "Commercial Real Estate",
      "link": ""
    },
    "location": {
      "text": "New York, NY",
      "link": ""
    },
    "headcount": {
      "text": "50-100",
      "link": ""
    },
    "role": {
      "text": "CEO",
      "link": ""
    },
    "page": 1
  }
]
```

### CSV Format

Direct import to Excel, Google Sheets, or any CRM!

| Company Name | Website | Industry | Location | Email | Phone | Role |
|--------------|---------|----------|----------|-------|-------|------|
| Acme Corp | acme.com | Real Estate | NY | contact@... | +1-555... | CEO |

---

## 🔧 Advanced Configuration

### Running Headless (No Visible Browser)

```bash
# In .env file
HEADLESS=true
```

### Adjust Page Size

```bash
# In .env file
PAGE_SIZE=50  # Instead of default 100
```

### Add localStorage Tokens (If Cookies Alone Don't Work)

If you get "Not authenticated" errors, you need localStorage tokens:

1. While logged into Muraena.ai, open browser console (F12)
2. Run: `localStorage`
3. Copy any auth-related keys
4. Add to scraper:

```python
LOCAL_STORAGE = {
    "authToken": "your_token_here",
    "user": '{"id": 31552, "email": "..."}',
}
```

---

## 🐛 Troubleshooting

### "Not authenticated" / Redirected to Login

**Cause**: Cookies expired or localStorage needed

**Solution**:
1. Export fresh cookies from your logged-in browser
2. Or add localStorage tokens (see Advanced Configuration)

### "No table found"

**Cause**: Page structure changed or wrong URL

**Solution**:
1. Check `screenshots/` folder to see what the scraper sees
2. Verify your TARGET_URL is correct
3. Check if you're logged in

### Reveal buttons not working

**Cause**: Button selector changed

**Solution**:
1. Inspect the reveal button in browser DevTools
2. Update button selectors in the script

### Slow scraping

**Cause**: Network delays or page loading time

**Solution**:
1. Increase `TIMEOUT` in .env
2. Reduce `PAGE_SIZE` for faster page loads
3. Run in headless mode (`HEADLESS=true`)

---

## 📈 Performance Tips

### Speed Optimization

```python
# In .env
HEADLESS=true         # Faster without rendering
PAGE_SIZE=50          # Smaller pages load faster
TIMEOUT=15000         # Reduce if site is fast
```

### Memory Optimization

For scraping 100+ pages:
- Process and export in batches
- Clear results after each batch
- Monitor memory usage

### Rate Limiting

Add delays to avoid detection:

```python
# Between pages
await asyncio.sleep(3)  # 3 second delay

# Between clicks
await asyncio.sleep(0.2)  # 200ms delay
```

---

## 🔒 Security Best Practices

### Protect Your Cookies

```bash
# Add to .gitignore
*.json
cookies.py
.env
screenshots/
```

### Never Commit Sensitive Data

- ❌ Don't commit cookies to Git
- ❌ Don't share your .env file
- ❌ Don't post screenshots publicly

### Rotate Credentials

- Cookies expire every 1-4 weeks
- Re-export when they expire
- Use temporary emails if testing

---

## 📚 Code Examples

### Custom Data Processing

```python
# After scraping
for result in scraper.all_results:
    company = result['companyName']['text']
    email = result['email']['text']
    
    # Your custom logic
    if 'CEO' in result['role']['text']:
        print(f"CEO email: {email}")
```

### Filter Results

```python
# Filter by location
us_companies = [
    r for r in results 
    if 'United States' in r['location']['text']
]

# Filter by headcount
large_companies = [
    r for r in results
    if '100+' in r['headcount']['text']
]
```

### Export to Database

```python
import sqlite3

conn = sqlite3.connect('companies.db')
cursor = conn.cursor()

for result in results:
    cursor.execute("""
        INSERT INTO companies (name, email, phone, industry)
        VALUES (?, ?, ?, ?)
    """, (
        result['companyName']['text'],
        result['email']['text'],
        result['phone']['text'],
        result['industry']['text']
    ))

conn.commit()
```

---

## 🆚 Comparison: Local vs Apify

| Feature | Local Scraper | Apify |
|---------|---------------|-------|
| **Cost** | 🟢 Free | 🔴 $$$  |
| **Speed** | 🟢 Fast | 🟡 Medium |
| **Control** | 🟢 Full | 🟡 Limited |
| **Setup** | 🟡 Medium | 🟢 Easy |
| **Debugging** | 🟢 Easy | 🔴 Hard |
| **Scaling** | 🟡 Your machine | 🟢 Cloud |
| **Privacy** | 🟢 All local | 🔴 Cloud |

**Verdict**: Use local scraper for 90% of use cases. Only use Apify if you need massive scale (1000+ pages).

---

## 🎯 Real-World Examples

### Example 1: Scrape All Real Estate Companies in US

```bash
# Set your filters in the URL, then:
python muraena_scraper_multipage.py --pages 50
```

### Example 2: Daily Automated Scraping

```bash
#!/bin/bash
# daily_scrape.sh

cd /path/to/scraper
source .venv/bin/activate

python muraena_scraper_multipage.py --pages 10

# Email results
mail -s "Daily Muraena Scrape" you@email.com < muraena_*.csv
```

Schedule with cron:
```bash
0 9 * * * /path/to/daily_scrape.sh
```

### Example 3: Custom Processing Pipeline

```bash
# 1. Scrape
python muraena_scraper_multipage.py --pages 20

# 2. Process with your custom script
python process_results.py muraena_multipage_*.json

# 3. Upload to CRM
python upload_to_crm.py processed_results.csv
```

---

## 🤝 Contributing

Want to improve this scraper? Here are some ideas:

- [ ] Add proxy rotation support
- [ ] Implement retry logic for failed pages
- [ ] Add progress bar (tqdm)
- [ ] Support for more export formats (XML, Parquet)
- [ ] Parallel page scraping
- [ ] Better error handling
- [ ] Unit tests

---

## 📄 License

This is open source! Use it however you want. Just remember:
- Respect Muraena.ai's Terms of Service
- Don't abuse their servers
- Use reasonable delays between requests

---

## 🆘 Support

**Having issues?**

1. Check the `screenshots/` folder
2. Look at the error logs
3. Verify your cookies are fresh
4. Check if TARGET_URL is correct

**Still stuck?**

- Check browser console (F12) while logged into Muraena.ai
- Try re-exporting cookies
- Test with `HEADLESS=false` to see what's happening

---

## 🎉 Success!

You now have a **professional-grade scraper** that:
- ✅ Costs $0
- ✅ Runs locally
- ✅ Gives you full control
- ✅ Exports to multiple formats
- ✅ Handles multi-page scraping
- ✅ Works with your existing auth

**No more Apify, no more cloud services, just pure open source scraping! 🚀**