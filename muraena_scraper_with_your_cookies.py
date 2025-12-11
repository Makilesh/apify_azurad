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

# Cookies extracted from EditThisCookie - ALL cookies included
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

# NOTE: You may need to add localStorage data if cookies alone don't work
# Check browser console for: localStorage.getItem('token') or similar

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
        
        // Wait for page to load
        log.info('Waiting for page to load...');
        await page.waitForLoadState('networkidle', {{ timeout: 15000 }});
        await page.waitForTimeout(3000);
        
        const currentUrl = page.url();
        log.info(`Current URL: ${{currentUrl}}`);
        
        // Check if we're logged in (not on login page)
        if (currentUrl.includes('login') || currentUrl.includes('signin')) {{
            log.error('❌ Not logged in - redirected to login page');
            log.error('The cookies may not be sufficient. You may need localStorage tokens.');
            
            // Try to check what's missing
            const cookies = await page.context().cookies();
            log.info(`Cookies present: ${{cookies.length}}`);
            
            await page.screenshot({{ path: 'not_authenticated.png', fullPage: true }});
            throw new Error('Not authenticated - session expired or localStorage needed');
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
            
            // Log page content for debugging
            const bodyText = await page.evaluate(() => document.body.innerText);
            log.info(`Page content preview: ${{bodyText.substring(0, 500)}}`);
            
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
                    cellCount: cells.length
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
        
        log.info('Adding cookies...');
        await page.context().addCookies(cookies);
        log.info(`✓ Added ${{cookies.length}} cookies`);
        
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
    """Run the Muraena.ai scraper with actual cookies from logged-in session"""
    print("🚀 Starting Muraena.ai scraper with your cookies...")
    print(f"📍 Target URL: {TARGET_URL[:80]}...")
    print()
    print("📝 Note: Your cookies include user_id: 31552 (you ARE logged in!)")
    print("   If this fails, we may need localStorage/sessionStorage tokens too.")
    print()
    
    try:
        # Run the Actor
        print("📤 Sending scraper configuration to Apify...")
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
            print("\nLast 40 lines of log:")
            print("=" * 60)
            print('\n'.join(log_content.split('\n')[-40:]))
            
            print("\n💡 If you see 'Not authenticated', you need localStorage tokens.")
            print("   Run the localStorage check in your browser console (see instructions).")
            
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("  MURAENA.AI SCRAPER - With Your Actual Cookies")
    print("=" * 60)
    
    results = run_scraper()
    
    if results:
        print("\n✅ Scraping completed successfully!")
        total_records = sum(len(item.get('results', [])) for item in results)
        print(f"📊 Total results: {total_records}")
    else:
        print("\n❌ Scraping failed.")
        print("\n🔍 Next steps:")
        print("1. Check the error log above")
        print("2. If you see 'Not authenticated', check localStorage in browser")
        print("3. Look at screenshots in Apify console")