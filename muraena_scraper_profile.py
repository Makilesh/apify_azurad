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
        print("Starting Muraena.ai Profile Scraper...")
        print(f"Target URL: {TARGET_URL}")
        print()

        playwright = await async_playwright().start()

        # Determine user data directory
        user_data_dir = CHROME_USER_DATA if USE_CHROME else EDGE_USER_DATA
        browser_name = "Chrome" if USE_CHROME else "Edge"

        print(f"Launching {browser_name} with your existing profile...")
        print(f"Profile directory: {user_data_dir}")
        print()
        print("IMPORTANT:")
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
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
                slow_mo=100  # Slow down operations slightly for stability
            )
            
            # Get the first page or create new one
            if len(self.context.pages) > 0:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()
            
            print("Browser launched with your profile!\n")
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error launching browser: {e}")
            print("\nCommon fixes:")

            if "Target page, context or browser has been closed" in error_msg:
                print("1. IMPORTANT: Close ALL Chrome/Edge windows completely")
                print("2. Check Task Manager and kill any Chrome/Edge processes")
                print("3. Then run this script again")
            else:
                print("1. Close Chrome/Edge completely (check Task Manager)")
                print("2. Make sure the user data directory exists")
                print("3. Try the other browser (set USE_CHROME = False)")
            raise
        
    async def navigate_to_target(self):
        """Navigate to the target search results page"""
        print(f"Navigating to target page...")
        
        try:
            response = await self.page.goto(TARGET_URL, wait_until='networkidle', timeout=TIMEOUT)
            print(f"   Status: {response.status}")
            
            # Check if we're logged in
            current_url = self.page.url
            print(f"   Current URL: {current_url}")
            
            if 'login' in current_url or 'signin' in current_url:
                print("\nYou're on the login page.")
                print("   Please login manually in the browser window.")
                print("   The session will be saved in your browser profile.")
                print()
                input("   Press ENTER after you've logged in...")

                # Check again
                current_url = self.page.url
                if 'login' in current_url or 'signin' in current_url:
                    print("Still on login page. Please login first.")
                    return False

            print("Successfully authenticated!\n")

            # Take screenshot
            os.makedirs('screenshots', exist_ok=True)
            await self.page.screenshot(path='screenshots/01_authenticated.png', full_page=True)
            print("   Screenshot saved: screenshots/01_authenticated.png\n")
            
            return True
            
        except Exception as e:
            print(f"Navigation error: {e}")
            return False
    
    async def switch_to_companies_tab(self):
        """Switch to the Companies tab (not People tab)"""
        print("Switching to Companies tab...")
        
        try:
            # Look for Companies tab/button
            companies_tab_selectors = [
                'a:has-text("Companies")',
                'button:has-text("Companies")',
                '[href*="companies"]',
                'div:has-text("Companies")',
            ]
            
            for selector in companies_tab_selectors:
                try:
                    tab = self.page.locator(selector).first
                    if await tab.count() > 0:
                        print(f"   Found Companies tab: {selector}")
                        await tab.click()
                        print("   Clicked Companies tab")
                        await self.page.wait_for_timeout(2000)

                        # Take screenshot
                        await self.page.screenshot(path='screenshots/02_companies_tab.png', full_page=True)
                        print("   Screenshot: screenshots/02_companies_tab.png\n")
                        return True
                except:
                    continue

            print("   Could not find Companies tab (might already be on it)\n")
            return True

        except Exception as e:
            print(f"   Error switching tabs: {e}\n")
            return True  # Continue anyway
    
    async def wait_for_companies(self):
        """Wait for the company list/cards to load"""
        print("Waiting for company list...")
        
        # Wait for dynamic content to load
        print("   Waiting for page to fully load...")
        await self.page.wait_for_timeout(5000)

        # Try to wait for loading spinner to disappear
        try:
            await self.page.wait_for_selector('.ant-spin', state='hidden', timeout=10000)
            print("   Loading complete")
        except:
            pass
        
        # Look for company cards/list items (not tables!)
        company_selectors = [
            '[class*="CompanyCard"]',
            '[class*="company-card"]',
            '[class*="CompanyRow"]',
            '[class*="company-row"]',
            '[class*="ResultCard"]',
            '[class*="result-card"]',
            '[class*="CompanyItem"]',
            '[class*="company-item"]',
            '[data-testid*="company"]',
            'div[class*="Result"]',
            'a[href*="/company/"]',
        ]
        
        for selector in company_selectors:
            try:
                print(f"   Trying selector: {selector}")
                await self.page.wait_for_selector(selector, timeout=3000)
                count = await self.page.locator(selector).count()
                if count > 0:
                    print(f"   Found {count} company items using: {selector}\n")
                    return selector
            except:
                continue
        
        # If specific selectors don't work, try to find the pattern
        print("\n   Analyzing page structure...")
        
        # Look for links that might be company links
        company_links = await self.page.evaluate('''() => {
            // Find all links that might be to company pages
            const links = Array.from(document.querySelectorAll('a'));
            const companyLinks = links.filter(a => 
                a.href.includes('/company/') || 
                a.textContent.includes('Properties') ||
                a.textContent.includes('LLC') ||
                a.textContent.includes('Inc')
            );
            return {
                count: companyLinks.length,
                sample: companyLinks.slice(0, 3).map(a => ({
                    text: a.textContent.trim(),
                    href: a.href,
                    className: a.className
                }))
            };
        }''')
        
        print(f"   Found {company_links['count']} potential company links")
        if company_links['count'] > 0:
            print(f"   Sample: {company_links['sample'][:2]}\n")
            return 'a[href*="/company/"]'  # Use company links as selector

        print("\nCould not find company list!")
        await self.page.screenshot(path='screenshots/02_no_companies_error.png', full_page=True)
        return None
    
    async def click_reveal_buttons(self):
        """Click all 'Reveal' buttons to uncover hidden data"""
        print("Looking for 'Reveal' buttons...")
        
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
            print(f"   Clicked {total_clicked} reveal buttons")
            await self.page.wait_for_timeout(2000)
            await self.page.screenshot(path='screenshots/04_after_reveal.png', full_page=True)
            print("   Screenshot saved: screenshots/04_after_reveal.png\n")
        else:
            print("   No reveal buttons found - data may already be visible\n")
    
    async def extract_company_data(self, company_selector):
        """Extract data from company cards/list (not a table!)"""
        print("Extracting data from company list...")
        
        # Take screenshot before extraction
        await self.page.screenshot(path='screenshots/03_before_extraction.png', full_page=True)
        
        # Extract data by parsing the row structure properly
        results = await self.page.evaluate(f"""
            () => {{
                // Find all company rows/cards
                const rows = document.querySelectorAll('[class*="CompanyRow"]');
                const companies = [];
                const seenCompanies = new Set(); // Track duplicates

                rows.forEach((row, idx) => {{
                    // Get all text content from the row
                    const text = row.innerText || '';
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l);

                    // Skip empty rows
                    if (lines.length < 3) return;

                    // Find company name link
                    const nameLink = row.querySelector('a[href*="/company/"]');
                    if (!nameLink) return; // Skip if no company link found

                    const companyName = nameLink.textContent.trim();
                    const companyUrl = nameLink.href;

                    // Skip duplicates based on company name
                    if (seenCompanies.has(companyName)) return;
                    seenCompanies.add(companyName);

                    // Find website link (external link, not to muraena.ai)
                    const links = Array.from(row.querySelectorAll('a[href]'));
                    const websiteLink = links.find(a =>
                        !a.href.includes('muraena.ai') &&
                        !a.href.includes('/company/') &&
                        a.href.startsWith('http')
                    );
                    const website = websiteLink ? websiteLink.href : '';

                    // Parse data from pipe-delimited allText
                    // Format: Company Name | website.com | Industry | Location, United States | Headcount
                    const allText = lines.join(' | ');
                    const parts = allText.split(' | ').map(p => p.trim());

                    let websiteText = '';
                    let industry = '';
                    let location = '';
                    let headcount = '';

                    // Parse each part
                    for (const part of parts) {{
                        // Skip company name
                        if (part === companyName) continue;

                        // Website is domain-like (has .com, .net, etc.)
                        if (!websiteText && /\\w+\\.\\w+/.test(part) && !part.includes(' ')) {{
                            websiteText = part;
                            continue;
                        }}

                        // Headcount is numeric range
                        if (!headcount && /^\\d+\\s*-\\s*\\d+$/.test(part)) {{
                            headcount = part;
                            continue;
                        }}

                        // Location contains "United States" or city/state pattern
                        if (!location && (part.includes('United States') || /[A-Z][a-z]+,\\s+[A-Z]/.test(part))) {{
                            // Must NOT be the same as industry (avoid the bug we saw)
                            if (!industry || part !== industry) {{
                                location = part;
                                continue;
                            }}
                        }}

                        // Industry - contains keywords or comma-separated items
                        if (!industry && (part.includes(',') ||
                            part.includes('Real Estate') || part.includes('Commercial') ||
                            part.includes('Property') || part.includes('Investment') ||
                            part.includes('Management') || part.includes('Leasing'))) {{
                            industry = part;
                            continue;
                        }}
                    }}

                    // Validate: must have at minimum company name and location
                    if (!companyName || (!location && !industry)) return;

                    companies.push({{
                        rowNumber: companies.length + 1,
                        companyName: {{ text: companyName, link: companyUrl }},
                        website: {{ text: websiteText, link: website || `https://${{websiteText}}` }},
                        industry: {{ text: industry }},
                        location: {{ text: location }},
                        headcount: {{ text: headcount }},
                        email: {{ text: 'REVEAL_REQUIRED' }},
                        phone: {{ text: 'REVEAL_REQUIRED' }},
                        role: {{ text: '' }},
                        allText: allText
                    }});
                }});

                return companies;
            }}
        """)
        
        # Filter out any remaining empty records
        self.results = [r for r in results if r['companyName']['text']]

        print(f"   Extracted {len(self.results)} companies\n")

        if self.results:
            print("Sample records:")
            for i, sample in enumerate(self.results[:3]):
                print(f"\n   {i+1}. {sample['companyName']['text']}")
                print(f"      Website: {sample['website']['text']}")
                print(f"      Industry: {sample['industry']['text']}")
                print(f"      Location: {sample['location']['text']}")
                print(f"      Headcount: {sample['headcount']['text']}")
        else:
            print("   No data extracted - check screenshots!\n")
            print("   Debug: Looking at page structure...")
            
            # Debug what we actually have
            debug_info = await self.page.evaluate('''() => {
                const rows = document.querySelectorAll('[class*="CompanyRow"]');
                return {
                    rowCount: rows.length,
                    sampleHTML: rows[0] ? rows[0].innerHTML.substring(0, 500) : 'N/A',
                    sampleText: rows[0] ? rows[0].innerText.substring(0, 200) : 'N/A'
                };
            }''')
            print(f"   Rows found: {debug_info['rowCount']}")
            print(f"   Sample text: {debug_info['sampleText']}\n")
        
        return self.results
    
    def save_results(self):
        """Save results to JSON and CSV files"""
        print("Saving results...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to JSON
        json_file = f'muraena_results_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"   JSON saved: {json_file}")
        
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

            print(f"   CSV saved: {csv_file}\n")
        
        return json_file, csv_file
    
    async def cleanup(self):
        """Close browser and cleanup"""
        if self.context:
            await self.context.close()
        print("Cleanup complete")
    
    async def run(self):
        """Main scraping workflow"""
        try:
            # Setup
            await self.setup()
            
            # Navigate
            if not await self.navigate_to_target():
                await self.cleanup()
                return False
            
            # Switch to Companies tab (important!)
            await self.switch_to_companies_tab()
            
            # Wait for company list
            company_selector = await self.wait_for_companies()
            if not company_selector:
                await self.cleanup()
                return False
            
            # Click reveal buttons
            await self.click_reveal_buttons()
            
            # Extract data
            await self.extract_company_data(company_selector)
            
            # Save results
            if self.results:
                self.save_results()
                print("Scraping completed successfully!")
                print(f"Total records extracted: {len(self.results)}")
            else:
                print("No data extracted")
            
            # Cleanup
            await self.cleanup()
            
            return True
            
        except Exception as e:
            print(f"\nError during scraping: {e}")
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
        print("\nTroubleshooting:")
        print("1. Close Chrome/Edge completely and try again")
        print("2. Check screenshots/ folder for debugging")
        print("3. Make sure you login in the browser when prompted")
        print("4. Try the other browser (change USE_CHROME setting)")


if __name__ == "__main__":
    asyncio.run(main())