"""
Muraena.ai Multi-Page Local Scraper

This version can scrape multiple pages automatically.

Features:
- Scrapes multiple pages (configurable range)
- Handles pagination automatically
- Progress tracking
- Deduplication
- Export to JSON/CSV/Excel

Usage:
    python muraena_scraper_multipage.py --start-page 1 --end-page 10
    python muraena_scraper_multipage.py --pages 5  # Scrape 5 pages starting from page 1
"""

import asyncio
import json
import os
import argparse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import csv
import pandas as pd

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv('BASE_URL', 'https://app.muraena.ai/companies_search/results')
HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
TIMEOUT = int(os.getenv('TIMEOUT', '30000'))
PAGE_SIZE = int(os.getenv('PAGE_SIZE', '100'))

# Cookies from your logged-in session
COOKIES = [
    {
        "name": "_ga",
        "value": "GA1.1.1825635158.1765359081",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": False
    },
    {
        "name": "_ga_8GNJYRECKW",
        "value": "GS2.1.s1765454279$o7$g0$t1765454279$j60$l0$h0",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": False
    },
    {
        "name": "_hjSessionUser_5015060",
        "value": "eyJpZCI6IjZiNGQzYjcwLWM4ODUtNTg4ZC1iMjM3LTczYTNlZWJkYzNkOSIsImNyZWF0ZWQiOjE3NjUzNTkwODE1MDcsImV4aXN0aW5nIjp0cnVlfQ==",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": True
    },
    {
        "name": "intercom-device-id-c4ozkspm",
        "value": "19096051-f3e5-48ab-a8ae-a9e06266cdb8",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": False
    },
    {
        "name": "intercom-session-c4ozkspm",
        "value": "QXpLeFAwVGkzQVRCemk4QnlDc2tqS2thVFlwZHNjcW92QlFqT1IxcHVJakt1d2Jkc1F0RUx6UXFCSi9ac0NBZkZkOEVGL2NPbkNXQkw3SHIyRjVZckdyK0RITTJmNU9kMDBGc1Z5Vlc5YUk9LS12dXdtY1NHUStRbi8zODNBM2s1SE53PT0=--f623796c596d81e6acb77815b3bf1c54d09cb90c",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": False
    },
    {
        "name": "mp_60a0f9774410aabfa2052f1f7e20abd9_mixpanel",
        "value": "%7B%22distinct_id%22%3A%20%2231552%22%2C%22%24device_id%22%3A%20%2219b0799d661633-0703e8cdbfaad8-26011a51-144000-19b0799d662c00%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%20%2231552%22%7D",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": False,
        "secure": False
    }
]

LOCAL_STORAGE = {}


class MultiPageScraper:
    def __init__(self, start_page=1, end_page=1):
        self.start_page = start_page
        self.end_page = end_page
        self.browser = None
        self.context = None
        self.page = None
        self.all_results = []
        self.seen_companies = set()  # For deduplication
        
    def build_url(self, page_num):
        """Build URL with page number and size"""
        # Parse existing URL and add/update page parameter
        if '?' in BASE_URL:
            base = BASE_URL.split('?')[0]
            params = BASE_URL.split('?')[1]
            
            # Update or add page parameter
            params_dict = {}
            for param in params.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params_dict[key] = value
            
            params_dict['page'] = str(page_num)
            params_dict['size'] = str(PAGE_SIZE)
            
            new_params = '&'.join([f"{k}={v}" for k, v in params_dict.items()])
            return f"{base}?{new_params}"
        else:
            return f"{BASE_URL}?page={page_num}&size={PAGE_SIZE}"
    
    async def setup(self):
        """Initialize browser"""
        print("🚀 Starting Multi-Page Scraper...")
        print(f"📄 Pages to scrape: {self.start_page} to {self.end_page}")
        print(f"📊 Page size: {PAGE_SIZE}")
        print()
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=HEADLESS,
            args=['--no-sandbox']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        await self.context.add_cookies(COOKIES)
        
        self.page = await self.context.new_page()
        
        if LOCAL_STORAGE:
            await self.page.goto('https://app.muraena.ai')
            for key, value in LOCAL_STORAGE.items():
                await self.page.evaluate(f'localStorage.setItem("{key}", {json.dumps(value)})')
        
        print("✅ Browser setup complete!\n")
    
    async def scrape_page(self, page_num):
        """Scrape a single page"""
        print(f"📄 Scraping page {page_num}...")
        
        url = self.build_url(page_num)
        print(f"   URL: {url}")
        
        try:
            # Navigate
            await self.page.goto(url, wait_until='networkidle', timeout=TIMEOUT)
            
            # Check authentication
            if 'login' in self.page.url:
                print("   ❌ Redirected to login - session expired")
                return []
            
            # Wait for table
            await self.page.wait_for_timeout(2000)
            
            table_selectors = ['table tbody tr', '.ant-table-tbody tr', 'tbody tr']
            row_selector = None
            
            for selector in table_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    count = await self.page.locator(selector).count()
                    if count > 0:
                        row_selector = selector
                        print(f"   ✓ Found {count} rows")
                        break
                except:
                    continue
            
            if not row_selector:
                print("   ⚠️  No table found")
                return []
            
            # Click reveal buttons
            reveal_buttons = await self.page.locator('button:has-text("Reveal")').all()
            if reveal_buttons:
                print(f"   🔓 Clicking {len(reveal_buttons)} reveal buttons...")
                for button in reveal_buttons[:50]:
                    try:
                        await button.click(timeout=300)
                        await self.page.wait_for_timeout(100)
                    except:
                        continue
                await self.page.wait_for_timeout(1500)
            
            # Extract data
            results = await self.page.evaluate(f"""
                (rowSelector) => {{
                    const rows = document.querySelectorAll(rowSelector);
                    const data = [];
                    
                    rows.forEach((row, idx) => {{
                        const cells = row.querySelectorAll('td');
                        if (cells.length === 0) return;
                        
                        const getCellData = (cell) => {{
                            if (!cell) return {{ text: '', link: '' }};
                            const link = cell.querySelector('a');
                            const text = cell.innerText?.trim() || '';
                            return {{ text: text, link: link ? link.href : '' }};
                        }};
                        
                        data.push({{
                            companyName: getCellData(cells[0]),
                            website: getCellData(cells[1]),
                            industry: getCellData(cells[2]),
                            location: getCellData(cells[3]),
                            headcount: getCellData(cells[4]),
                            email: getCellData(cells[5]),
                            phone: getCellData(cells[6]),
                            role: getCellData(cells[7]),
                            page: {page_num}
                        }});
                    }});
                    
                    return data;
                }}
            """, row_selector)
            
            # Deduplicate
            new_results = []
            for result in results:
                company_key = f"{result['companyName']['text']}_{result['email']['text']}"
                if company_key not in self.seen_companies:
                    self.seen_companies.add(company_key)
                    new_results.append(result)
            
            print(f"   ✅ Extracted {len(results)} records ({len(new_results)} new)\n")
            
            return new_results
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            return []
    
    async def run(self):
        """Main scraping workflow"""
        try:
            await self.setup()
            
            # Scrape each page
            for page_num in range(self.start_page, self.end_page + 1):
                page_results = await self.scrape_page(page_num)
                self.all_results.extend(page_results)
                
                # Small delay between pages
                if page_num < self.end_page:
                    await asyncio.sleep(2)
            
            # Save results
            if self.all_results:
                self.save_results()
                print(f"✅ Scraping completed!")
                print(f"📊 Total records: {len(self.all_results)}")
            else:
                print("⚠️  No data extracted")
            
            await self.browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if self.browser:
                await self.browser.close()
            return False
    
    def save_results(self):
        """Save to multiple formats"""
        print("\n💾 Saving results...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON
        json_file = f'muraena_multipage_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, indent=2, ensure_ascii=False)
        print(f"   ✓ JSON: {json_file}")
        
        # CSV
        csv_file = f'muraena_multipage_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.all_results:
                writer = csv.DictWriter(f, fieldnames=[
                    'page', 'companyName', 'website', 'industry', 'location',
                    'headcount', 'email', 'phone', 'role', 'companyLink', 'websiteLink'
                ])
                writer.writeheader()
                
                for row in self.all_results:
                    writer.writerow({
                        'page': row['page'],
                        'companyName': row['companyName']['text'],
                        'website': row['website']['text'],
                        'industry': row['industry']['text'],
                        'location': row['location']['text'],
                        'headcount': row['headcount']['text'],
                        'email': row['email']['text'],
                        'phone': row['phone']['text'],
                        'role': row['role']['text'],
                        'companyLink': row['companyName']['link'],
                        'websiteLink': row['website']['link']
                    })
        
        print(f"   ✓ CSV: {csv_file}")
        
        # Excel
        try:
            excel_file = f'muraena_multipage_{timestamp}.xlsx'
            df = pd.DataFrame([
                {
                    'Page': row['page'],
                    'Company Name': row['companyName']['text'],
                    'Website': row['website']['text'],
                    'Industry': row['industry']['text'],
                    'Location': row['location']['text'],
                    'Headcount': row['headcount']['text'],
                    'Email': row['email']['text'],
                    'Phone': row['phone']['text'],
                    'Role': row['role']['text'],
                    'Company Link': row['companyName']['link'],
                    'Website Link': row['website']['link']
                }
                for row in self.all_results
            ])
            df.to_excel(excel_file, index=False)
            print(f"   ✓ Excel: {excel_file}\n")
        except Exception as e:
            print(f"   ⚠️  Could not save Excel: {e}\n")


def main():
    parser = argparse.ArgumentParser(description='Muraena.ai Multi-Page Scraper')
    parser.add_argument('--start-page', type=int, default=1, help='Start page number')
    parser.add_argument('--end-page', type=int, help='End page number')
    parser.add_argument('--pages', type=int, help='Number of pages to scrape (starting from page 1)')
    
    args = parser.parse_args()
    
    # Determine page range
    if args.pages:
        start_page = 1
        end_page = args.pages
    else:
        start_page = args.start_page
        end_page = args.end_page if args.end_page else args.start_page
    
    print("=" * 60)
    print("  MURAENA.AI MULTI-PAGE SCRAPER")
    print("=" * 60)
    print()
    
    scraper = MultiPageScraper(start_page, end_page)
    asyncio.run(scraper.run())


if __name__ == "__main__":
    main()