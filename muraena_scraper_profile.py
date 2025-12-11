"""
Muraena.ai Scraper - Using Persistent Browser Profile

This version uses your existing Chrome/Edge profile where you're already logged in.
No need to extract cookies or localStorage!

Features:
- Uses your existing browser profile (already logged in!)
- No cookie/localStorage extraction needed
- Scrapes company data from search results
- Exports to JSON/CSV

Requirements:
    pip install playwright pandas
    playwright install chromium

Usage:
    python muraena_scraper_profile.py
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
TIMEOUT = int(os.getenv('TIMEOUT', '30000'))

# Chrome/Edge user data directory
# Windows default paths:
CHROME_USER_DATA = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data')
EDGE_USER_DATA = os.path.expanduser('~/AppData/Local/Microsoft/Edge/User Data')

# Choose which browser profile to use
USE_CHROME = True  # Set to False to use Edge instead


class MuraenaProfileScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        
    async def setup(self):
        """Initialize browser with existing profile"""
        print("🚀 Starting Muraena.ai Profile Scraper...")
        print(f"📍 Target URL: {TARGET_URL}")
        print()
        
        playwright = await async_playwright().start()
        
        # Determine user data directory
        user_data_dir = CHROME_USER_DATA if USE_CHROME else EDGE_USER_DATA
        browser_name = "Chrome" if USE_CHROME else "Edge"
        
        print(f"🌐 Launching {browser_name} with your existing profile...")
        print(f"📂 Profile directory: {user_data_dir}")
        print()
        print("⚠️  IMPORTANT:")
        print("   1. If browser is already open, close it first!")
        print("   2. Browser will open and you should ALREADY be logged in")
        print("   3. If not logged in, login once and the session will persist")
        print()
        
        try:
            # Launch browser with persistent context (your existing profile)
            self.context = await playwright.chromium.launch_persistent_context(
                user_data_dir,
                headless=False,  # Must be False when using user data
                channel='chrome' if USE_CHROME else 'msedge',
                viewport={'width': 1920, 'height': 1080},
                args=['--no-sandbox']
            )
            
            # Get the first page or create new one
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()
            
            print("✅ Browser launched with your profile!\n")
            
        except Exception as e:
            print(f"❌ Error launching browser: {e}")
            print("\n💡 Common fixes:")
            print("1. Close Chrome/Edge completely (check Task Manager)")
            print("2. Make sure the user data directory exists")
            print("3. Try the other browser (set USE_CHROME = False)")
            raise
        
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
                print("\n⚠️  You're on the login page.")
                print("   Please login manually in the browser window.")
                print("   The session will be saved in your browser profile.")
                print()
                input("   Press ENTER after you've logged in...")
                
                # Check again
                current_url = self.page.url
                if 'login' in current_url or 'signin' in current_url:
                    print("❌ Still on login page. Please login first.")
                    return False
            
            print("✅ Successfully authenticated!\n")
            
            # Take screenshot
            os.makedirs('screenshots', exist_ok=True)
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
                    
                    for i, button in enumerate(buttons[:50]):
                        try:
                            await button.click(timeout=500)
                            total_clicked += 1
                            await self.page.wait_for_timeout(200)
                        except:
                            continue
            except:
                continue
        
        if total_clicked > 0:
            print(f"   ✓ Clicked {total_clicked} reveal buttons")
            await self.page.wait_for_timeout(2000)
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
        if self.context:
            await self.context.close()
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
    print("=" * 60)
    print("  MURAENA.AI PROFILE SCRAPER - No Cookie Extraction!")
    print("=" * 60)
    print()
    
    scraper = MuraenaProfileScraper()
    success = await scraper.run()
    
    if not success:
        print("\n💡 Troubleshooting:")
        print("1. Close Chrome/Edge completely and try again")
        print("2. Check screenshots/ folder for debugging")
        print("3. Make sure you login in the browser when prompted")
        print("4. Try the other browser (change USE_CHROME setting)")


if __name__ == "__main__":
    asyncio.run(main())