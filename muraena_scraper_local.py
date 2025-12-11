"""
Muraena.ai Local Scraper - No Apify Required!

This script uses Playwright to scrape Muraena.ai data directly from your machine.
It can use your existing browser session (with cookies) or login automatically.

Features:
- Uses your existing authentication (cookies + localStorage)
- Scrapes company data from search results
- Clicks "Reveal" buttons automatically
- Exports to JSON/CSV
- Much faster than Apify
- No costs!

Requirements:
    pip install playwright pandas openpyxl
    playwright install chromium

Usage:
    python muraena_scraper_local.py
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import csv

# Load environment variables
load_dotenv()

# Configuration
TARGET_URL = os.getenv('TARGET_URL', 'https://app.muraena.ai/companies_search/results')
HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
TIMEOUT = int(os.getenv('TIMEOUT', '30000'))

# Your cookies from EditThisCookie
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

# localStorage data (add this if cookies alone don't work)
LOCAL_STORAGE = {
    # Example:
    # "authToken": "your_token_here",
    # "user": '{"id": 31552, "email": "..."}',
}


class MuraenaScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        
    async def setup(self):
        """Initialize browser and authentication"""
        print("🚀 Starting Muraena.ai Local Scraper...")
        print(f"📍 Target URL: {TARGET_URL}")
        print(f"👁️  Headless mode: {HEADLESS}")
        print()
        
        playwright = await async_playwright().start()
        
        # Launch browser
        print("🌐 Launching browser...")
        self.browser = await playwright.chromium.launch(
            headless=HEADLESS,
            args=['--no-sandbox']
        )
        
        # Create context with cookies
        print("🍪 Setting up authentication...")
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Add cookies
        await self.context.add_cookies(COOKIES)
        print(f"   ✓ Added {len(COOKIES)} cookies")
        
        # Create page
        self.page = await self.context.new_page()
        
        # Set localStorage if provided
        if LOCAL_STORAGE:
            print(f"   ✓ Setting {len(LOCAL_STORAGE)} localStorage items...")
            await self.page.goto('https://app.muraena.ai')
            for key, value in LOCAL_STORAGE.items():
                await self.page.evaluate(f'localStorage.setItem("{key}", {json.dumps(value)})')
        
        print("✅ Browser setup complete!\n")
        
    async def navigate_to_target(self):
        """Navigate to the target search results page"""
        print(f"🔍 Navigating to target page...")
        
        try:
            response = await self.page.goto(TARGET_URL, wait_until='networkidle', timeout=TIMEOUT)
            print(f"   Status: {response.status}")
            
            # Check if we're logged in
            current_url = self.page.url
            print(f"   Current URL: {current_url}")
            
            if 'login' in current_url or 'signin' in current_url:
                print("\n❌ ERROR: Redirected to login page!")
                print("   Your session may have expired or localStorage tokens are needed.")
                print("\n💡 Solution: Run extract_storage.html to get localStorage tokens")
                return False
            
            print("✅ Successfully authenticated!\n")
            
            # Take screenshot
            await self.page.screenshot(path='screenshots/01_authenticated.png', full_page=True)
            print("   📸 Screenshot saved: screenshots/01_authenticated.png\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False
    
    async def wait_for_table(self):
        """Wait for the results table to load"""
        print("⏳ Waiting for results table...")
        
        table_selectors = [
            'table tbody tr',
            '.ant-table-tbody tr',
            '[class*="Table"] tbody tr',
            'tbody tr'
        ]
        
        for selector in table_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=10000)
                count = await self.page.locator(selector).count()
                print(f"   ✓ Found {count} rows using selector: {selector}\n")
                return selector
            except:
                continue
        
        print("❌ No table found!")
        await self.page.screenshot(path='screenshots/02_no_table_error.png', full_page=True)
        print("   📸 Screenshot saved: screenshots/02_no_table_error.png\n")
        return None
    
    async def click_reveal_buttons(self):
        """Click all 'Reveal' buttons to uncover hidden data"""
        print("🔓 Looking for 'Reveal' buttons...")
        
        await self.page.screenshot(path='screenshots/03_before_reveal.png', full_page=True)
        
        # Try different button selectors
        reveal_selectors = [
            'button:has-text("Reveal")',
            'button:has-text("Show")',
            'button[class*="reveal"]',
            'button[class*="show"]'
        ]
        
        total_clicked = 0
        
        for selector in reveal_selectors:
            try:
                buttons = await self.page.locator(selector).all()
                
                if buttons:
                    print(f"   Found {len(buttons)} buttons with selector: {selector}")
                    
                    for i, button in enumerate(buttons[:50]):  # Limit to 50 to avoid timeouts
                        try:
                            await button.click(timeout=500)
                            total_clicked += 1
                            await self.page.wait_for_timeout(200)  # Small delay between clicks
                        except:
                            continue
            except:
                continue
        
        if total_clicked > 0:
            print(f"   ✓ Clicked {total_clicked} reveal buttons")
            await self.page.wait_for_timeout(2000)  # Wait for data to load
            await self.page.screenshot(path='screenshots/04_after_reveal.png', full_page=True)
            print("   📸 Screenshot saved: screenshots/04_after_reveal.png\n")
        else:
            print("   ℹ️  No reveal buttons found - data may already be visible\n")
    
    async def extract_table_data(self, row_selector):
        """Extract data from the table"""
        print("📊 Extracting data from table...")
        
        # JavaScript to extract table data
        results = await self.page.evaluate(f"""
            (rowSelector) => {{
                const rows = document.querySelectorAll(rowSelector);
                const data = [];
                
                rows.forEach((row, idx) => {{
                    const cells = row.querySelectorAll('td');
                    if (cells.length === 0) return;
                    
                    const getCellData = (cell) => {{
                        if (!cell) return {{ text: '', link: '', hasButton: false }};
                        
                        const link = cell.querySelector('a');
                        const button = cell.querySelector('button');
                        const text = cell.innerText?.trim() || '';
                        
                        return {{
                            text: text,
                            link: link ? link.href : '',
                            hasButton: !!button
                        }};
                    }};
                    
                    const rowData = {{
                        rowNumber: idx + 1,
                        companyName: getCellData(cells[0]),
                        website: getCellData(cells[1]),
                        industry: getCellData(cells[2]),
                        location: getCellData(cells[3]),
                        headcount: getCellData(cells[4]),
                        email: getCellData(cells[5]),
                        phone: getCellData(cells[6]),
                        role: getCellData(cells[7]),
                        additional: getCellData(cells[8]),
                        cellCount: cells.length
                    }};
                    
                    data.push(rowData);
                }});
                
                return data;
            }}
        """, row_selector)
        
        self.results = results
        print(f"   ✓ Extracted {len(results)} records\n")
        
        if results:
            print("📋 Sample record:")
            sample = results[0]
            print(f"   Company: {sample['companyName']['text']}")
            print(f"   Email: {sample['email']['text']}")
            print(f"   Phone: {sample['phone']['text']}")
            print(f"   Location: {sample['location']['text']}\n")
        
        return results
    
    def save_results(self):
        """Save results to JSON and CSV files"""
        print("💾 Saving results...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to JSON
        json_file = f'muraena_results_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"   ✓ JSON saved: {json_file}")
        
        # Save to CSV
        csv_file = f'muraena_results_{timestamp}.csv'
        if self.results:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Row', 'Company Name', 'Website', 'Industry', 'Location',
                    'Headcount', 'Email', 'Phone', 'Role', 'Company Link', 'Website Link'
                ])
                
                # Data
                for row in self.results:
                    writer.writerow([
                        row['rowNumber'],
                        row['companyName']['text'],
                        row['website']['text'],
                        row['industry']['text'],
                        row['location']['text'],
                        row['headcount']['text'],
                        row['email']['text'],
                        row['phone']['text'],
                        row['role']['text'],
                        row['companyName']['link'],
                        row['website']['link']
                    ])
            
            print(f"   ✓ CSV saved: {csv_file}\n")
        
        return json_file, csv_file
    
    async def cleanup(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        print("🧹 Cleanup complete")
    
    async def run(self):
        """Main scraping workflow"""
        try:
            # Setup
            await self.setup()
            
            # Navigate
            if not await self.navigate_to_target():
                await self.cleanup()
                return False
            
            # Wait for table
            row_selector = await self.wait_for_table()
            if not row_selector:
                await self.cleanup()
                return False
            
            # Click reveal buttons
            await self.click_reveal_buttons()
            
            # Extract data
            await self.extract_table_data(row_selector)
            
            # Save results
            if self.results:
                self.save_results()
                print("✅ Scraping completed successfully!")
                print(f"📊 Total records extracted: {len(self.results)}")
            else:
                print("⚠️  No data extracted")
            
            # Cleanup
            await self.cleanup()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            
            await self.cleanup()
            return False


async def main():
    """Entry point"""
    # Create screenshots directory
    os.makedirs('screenshots', exist_ok=True)
    
    print("=" * 60)
    print("  MURAENA.AI LOCAL SCRAPER - Open Source Edition")
    print("=" * 60)
    print()
    
    scraper = MuraenaScraper()
    success = await scraper.run()
    
    if not success:
        print("\n💡 Troubleshooting:")
        print("1. Check screenshots/ folder for debugging")
        print("2. If you see 'Not authenticated', run extract_storage.html")
        print("3. Add localStorage tokens to LOCAL_STORAGE in this script")
        print("4. Make sure TARGET_URL is correct in .env")


if __name__ == "__main__":
    asyncio.run(main())