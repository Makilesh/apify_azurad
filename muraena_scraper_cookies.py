import os
import time
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
TARGET_URL = os.getenv('TARGET_URL')

# Validate required environment variables
if not APIFY_API_TOKEN:
    raise ValueError("❌ APIFY_API_TOKEN not found in .env file")
if not TARGET_URL:
    raise ValueError("❌ TARGET_URL not found in .env file")

# Initialize the ApifyClient
client = ApifyClient(APIFY_API_TOKEN)

# IMPORTANT: Replace these with your actual cookies after manual login
# See instructions below on how to get these
COOKIES = [
    {
        "name": "your_session_cookie_name",
        "value": "your_session_cookie_value",
        "domain": ".muraena.ai",
        "path": "/",
        "httpOnly": True,
        "secure": True
    },
    # Add more cookies if needed
]

# Configuration for Playwright Scraper
run_input = {
    "browserLog": True,
    "closeCookieModals": True,
    "debugLog": True,
    "downloadCss": False,
    "downloadMedia": False,
    "excludes": [
        {"glob": "/**/*.{png,jpg,jpeg,pdf,svg,gif,woff,woff2}"}
    ],
    "globs": [
        {"glob": "https://app.muraena.ai/**"}
    ],
    "headless": False,
    "ignoreCorsAndCsp": False,
    "ignoreSslErrors": False,
    "keepUrlFragments": False,
    "launcher": "chromium",
    "maxConcurrency": 1,
    "maxRequestRetries": 3,
    "maxRequestsPerCrawl": 100,
    "pageFunction": f"""async function pageFunction(context) {{
    const {{ page, request, log }} = context;
    
    try {{
        log.info('=== STARTING DATA EXTRACTION ===');
        
        // Add cookies if they were set in preNavigationHooks
        log.info('Waiting for page to load...');
        await page.waitForLoadState('networkidle', {{ timeout: 15000 }});
        await page.waitForTimeout(3000);
        
        const currentUrl = page.url();
        log.info(`Current URL: ${{currentUrl}}`);
        
        // Check if we're logged in (not on login page)
        if (currentUrl.includes('login') || currentUrl.includes('signin')) {{
            log.error('❌ Not logged in - redirected to login page');
            log.error('Your session cookies may have expired. Please update them.');
            throw new Error('Not authenticated - session expired');
        }}
        
        log.info('✅ Successfully authenticated!');
        await page.screenshot({{ path: 'authenticated_page.png', fullPage: true }});
        
        log.info('=== SCRAPING DATA ===');
        
        // Wait for table to load
        const tableSelectors = [
            'table tbody tr',
            '.ant-table-tbody tr',
            '[class*="Table"] tbody tr',
            'tbody tr'
        ];
        
        let rowsSelector = null;
        for (const selector of tableSelectors) {{
            try {{
                await page.waitForSelector(selector, {{ timeout: 10000 }});
                const rowCount = await page.$$eval(selector, rows => rows.length);
                log.info(`✓ Found ${{rowCount}} rows using: ${{selector}}`);
                rowsSelector = selector;
                break;
            }} catch (e) {{
                log.info(`Selector not found: ${{selector}}`);
            }}
        }}
        
        if (!rowsSelector) {{
            log.error('❌ No table found');
            await page.screenshot({{ path: 'no_table_error.png', fullPage: true }});
            throw new Error('No results table found');
        }}
        
        await page.screenshot({{ path: 'before_reveal.png', fullPage: true }});
        
        // Click reveal buttons to uncover contact info
        log.info('Looking for "Reveal" buttons...');
        const revealButtons = await page.$$('button:has-text("Reveal"), button:has-text("Show")');
        
        if (revealButtons.length > 0) {{
            log.info(`Found ${{revealButtons.length}} reveal buttons, clicking them...`);
            
            for (let i = 0; i < Math.min(revealButtons.length, 50); i++) {{
                try {{
                    await revealButtons[i].click();
                    await page.waitForTimeout(300);
                }} catch (e) {{
                    log.info(`Could not click button ${{i}}: ${{e.message}}`);
                }}
            }}
            
            log.info('✓ Clicked reveal buttons');
            await page.waitForTimeout(2000);
            await page.screenshot({{ path: 'after_reveal.png', fullPage: true }});
        }} else {{
            log.info('No reveal buttons found - data may already be visible');
        }}
        
        // Extract data from table
        const results = await page.$$eval(rowsSelector, (rows) => {{
            return rows.map((row, idx) => {{
                const cells = row.querySelectorAll('td');
                if (cells.length === 0) return null;
                
                // Extract text content from cells
                const getCellText = (cell) => {{
                    if (!cell) return '';
                    // Try to get link href if present
                    const link = cell.querySelector('a');
                    const button = cell.querySelector('button');
                    
                    if (link && link.href) {{
                        return {{ text: cell.innerText?.trim() || '', link: link.href }};
                    }}
                    if (button) {{
                        return {{ text: cell.innerText?.trim() || '', hasButton: true }};
                    }}
                    return {{ text: cell.innerText?.trim() || '' }};
                }};
                
                return {{
                    rowNumber: idx + 1,
                    companyName: getCellText(cells[0]),
                    website: getCellText(cells[1]),
                    industry: getCellText(cells[2]),
                    location: getCellText(cells[3]),
                    headcount: getCellText(cells[4]),
                    email: getCellText(cells[5]),
                    phone: getCellText(cells[6]),
                    role: getCellText(cells[7]),
                    additionalData: getCellText(cells[8]),
                    cellCount: cells.length,
                    rawHTML: row.innerHTML
                }};
            }}).filter(item => item !== null);
        }});
        
        log.info(`✅ Extracted ${{results.length}} records`);
        
        if (results.length > 0) {{
            log.info('Sample record: ' + JSON.stringify(results[0], null, 2));
        }}
        
        return {{
            success: true,
            results,
            pageUrl: page.url(),
            totalRecords: results.length,
            scrapedAt: new Date().toISOString()
        }};
        
    }} catch (error) {{
        log.error(`❌ ERROR: ${{error.message}}`);
        await page.screenshot({{ path: 'error_screenshot.png', fullPage: true }});
        throw error;
    }}
}}""",
    "preNavigationHooks": f"""[
    async (crawlingContext, gotoOptions) => {{
        const {{ page, log }} = crawlingContext;
        
        // Set custom headers
        await page.setExtraHTTPHeaders({{
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }});
        
        // Add authentication cookies
        const cookies = {json.dumps(COOKIES)};
        
        if (cookies && cookies.length > 0 && cookies[0].value !== 'your_session_cookie_value') {{
            log.info('Adding authentication cookies...');
            await page.context().addCookies(cookies);
            log.info('✓ Cookies added');
        }} else {{
            log.warn('⚠️ No valid cookies configured - login may be required');
        }}
        
        log.info('✓ Pre-navigation setup completed');
    }}
]""",
    "postNavigationHooks": """[
    async (crawlingContext) => {
        const { page, log } = crawlingContext;
        
        await page.waitForTimeout(2000);
        log.info('✓ Post-navigation completed');
    }
]""",
    "proxyConfiguration": {
        "useApifyProxy": True,
        "apifyProxyGroups": ["RESIDENTIAL"]
    },
    "respectRobotsTxtFile": False,
    "startUrls": [
        {
            "url": TARGET_URL
        }
    ],
    "useChrome": False,
    "waitUntil": "networkidle"
}


def run_scraper():
    """Run the Muraena.ai scraper with session cookies"""
    print("🚀 Starting Muraena.ai scraper (Cookie-based authentication)...")
    print(f"📍 Target URL: {TARGET_URL[:80]}...")
    
    # Check if cookies are configured
    if COOKIES[0]['value'] == 'your_session_cookie_value':
        print("\n⚠️  WARNING: Cookies not configured!")
        print("=" * 60)
        print("Please follow these steps to get your session cookies:")
        print()
        print("1. Open Chrome/Firefox and go to https://app.muraena.ai")
        print("2. Login manually (check your email for magic link)")
        print("3. Once logged in, open Developer Tools (F12)")
        print("4. Go to 'Application' tab (Chrome) or 'Storage' tab (Firefox)")
        print("5. Click 'Cookies' → 'https://app.muraena.ai'")
        print("6. Look for session/auth cookies (usually named like:")
        print("   - 'session', 'auth_token', 'access_token', etc.")
        print("7. Copy the Name, Value, Domain, Path for each cookie")
        print("8. Update the COOKIES list in this script")
        print()
        print("Example:")
        print('COOKIES = [')
        print('    {')
        print('        "name": "session",')
        print('        "value": "abc123def456...",')
        print('        "domain": ".muraena.ai",')
        print('        "path": "/",')
        print('        "httpOnly": True,')
        print('        "secure": True')
        print('    }')
        print(']')
        print("=" * 60)
        
        response = input("\nDo you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return None
    
    try:
        # Run the Actor
        print("\n📤 Sending scraper configuration to Apify...")
        run = client.actor("apify/playwright-scraper").call(run_input=run_input)
        
        print(f"✅ Actor run started: {run['id']}")
        print(f"🔗 View run: https://console.apify.com/actors/runs/{run['id']}")
        
        # Wait for completion
        print("⏳ Waiting for scraper to complete...")
        
        run_client = client.run(run['id'])
        
        while True:
            run_info = run_client.get()
            status = run_info['status']
            
            print(f"📊 Status: {status}")
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break
            
            time.sleep(10)
        
        if status == 'SUCCEEDED':
            print("✅ Scraper completed successfully!")
            
            # Fetch results
            print("📥 Fetching results...")
            dataset_id = run['defaultDatasetId']
            dataset_client = client.dataset(dataset_id)
            
            items = list(dataset_client.iterate_items())
            
            if items:
                print(f"\n📊 RESULTS: Found {len(items)} item(s)")
                
                # Save results
                output_file = 'muraena_results.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Results saved to: {output_file}")
                
                # Display summary
                for idx, item in enumerate(items):
                    if 'results' in item:
                        print(f"\n📋 Item {idx + 1}:")
                        print(f"   Total records: {item.get('totalRecords', 0)}")
                        print(f"   Page URL: {item.get('pageUrl', 'N/A')}")
                        print(f"   Scraped at: {item.get('scrapedAt', 'N/A')}")
                        
                        if item['results']:
                            print(f"\n   Sample records:")
                            for i, record in enumerate(item['results'][:3]):
                                company = record.get('companyName', {})
                                print(f"   {i+1}. {company.get('text', 'N/A') if isinstance(company, dict) else company}")
                                
                                email = record.get('email', {})
                                phone = record.get('phone', {})
                                
                                email_text = email.get('text', 'N/A') if isinstance(email, dict) else email
                                phone_text = phone.get('text', 'N/A') if isinstance(phone, dict) else phone
                                
                                print(f"      Email: {email_text}")
                                print(f"      Phone: {phone_text}")
                
                return items
            else:
                print("⚠️ No results found")
                return []
        
        else:
            print(f"❌ Scraper failed with status: {status}")
            
            # Get logs
            print("\n📜 Fetching logs...")
            log_client = client.log(run['id'])
            log_content = log_client.get()
            
            log_file = 'scraper_error.log'
            with open(log_file, 'w') as f:
                f.write(log_content)
            
            print(f"📝 Error log saved to: {log_file}")
            print("\nLast 30 lines of log:")
            print("=" * 60)
            print('\n'.join(log_content.split('\n')[-30:]))
            
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("  MURAENA.AI SCRAPER - Cookie-Based Authentication")
    print("=" * 60)
    
    results = run_scraper()
    
    if results:
        print("\n✅ Scraping completed successfully!")
        total_records = sum(len(item.get('results', [])) for item in results)
        print(f"📊 Total results: {total_records}")
    else:
        print("\n❌ Scraping failed. Check the logs above.")