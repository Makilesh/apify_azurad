import os
import time
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
MURAENA_EMAIL = os.getenv('MURAENA_EMAIL')
MURAENA_PASSWORD = os.getenv('MURAENA_PASSWORD')
TARGET_URL = os.getenv('TARGET_URL')

# Validate required environment variables
if not APIFY_API_TOKEN:
    raise ValueError("❌ APIFY_API_TOKEN not found in .env file")
if not MURAENA_EMAIL:
    raise ValueError("❌ MURAENA_EMAIL not found in .env file")
if not MURAENA_PASSWORD:
    raise ValueError("❌ MURAENA_PASSWORD not found in .env file")
if not TARGET_URL:
    raise ValueError("❌ TARGET_URL not found in .env file")

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)

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
    
    if (request.userData.label === 'LOGIN') {{
        log.info('=== STARTING LOGIN PROCESS ===');
        
        try {{
            await page.waitForLoadState('networkidle', {{ timeout: 15000 }});
            await page.waitForTimeout(3000);
            
            log.info('Looking for login form...');
            await page.waitForSelector('#registration', {{ timeout: 10000 }});
            log.info('✓ Login form found');
            
            await page.waitForTimeout(2000);
            
            // STEP 1: Fill email
            const emailInputs = await page.$$('#registration input[type="text"], #registration input[type="email"]');
            log.info(`Found ${{emailInputs.length}} email input fields`);
            
            if (emailInputs.length < 1) {{
                throw new Error('No email input field found');
            }}
            
            log.info('Filling email field...');
            await emailInputs[0].fill('{MURAENA_EMAIL}');
            await page.waitForTimeout(1000);
            log.info('✓ Email filled');
            
            await page.screenshot({{ path: 'step1_email_filled.png', fullPage: true }});
            
            // Click Continue button
            const continueSelectors = [
                '#registration button:has-text("Continue")',
                '#registration button:has-text("Next")',
                '#registration button[type="submit"]',
                '#registration button.Button_type_primary__yGndD',
                '#registration button'
            ];
            
            let continueBtnClicked = false;
            for (const selector of continueSelectors) {{
                try {{
                    const button = await page.$(selector);
                    if (button) {{
                        const buttonText = await button.innerText();
                        log.info(`Found button: "${{buttonText}}"`);
                        await button.click();
                        log.info(`✓ Clicked: ${{selector}}`);
                        continueBtnClicked = true;
                        break;
                    }}
                }} catch (e) {{
                    // Try next
                }}
            }}
            
            if (!continueBtnClicked) {{
                log.info('No continue button found, checking if password field exists...');
            }} else {{
                log.info('Waiting for password field...');
                await page.waitForTimeout(3000);
            }}
            
            await page.screenshot({{ path: 'step2_after_continue.png', fullPage: true }});
            
            // STEP 2: Fill password
            await page.waitForTimeout(2000);
            const passwordInputs = await page.$$('#registration input[type="password"]');
            log.info(`Found ${{passwordInputs.length}} password fields`);
            
            if (passwordInputs.length === 0) {{
                const allInputs = await page.$$('#registration input');
                log.info(`Total inputs: ${{allInputs.length}}`);
                
                if (allInputs.length >= 2) {{
                    log.info('Using second input as password...');
                    await allInputs[1].fill('{MURAENA_PASSWORD}');
                    await page.waitForTimeout(1000);
                    log.info('✓ Password filled (second input)');
                }} else {{
                    log.info('Only 1 input - might be single-step login');
                }}
            }} else {{
                log.info('Filling password field...');
                await passwordInputs[0].fill('{MURAENA_PASSWORD}');
                await page.waitForTimeout(1000);
                log.info('✓ Password filled');
            }}
            
            await page.screenshot({{ path: 'step3_before_submit.png', fullPage: true }});
            
            // STEP 3: Submit
            const submitSelectors = [
                '#registration button:has-text("Sign in")',
                '#registration button:has-text("Log in")',
                '#registration button:has-text("Login")',
                '#registration button[type="submit"]',
                '#registration button.SignInForm_loginButton__fQCQ3',
                '#registration button'
            ];
            
            let submitClicked = false;
            for (const selector of submitSelectors) {{
                try {{
                    const button = await page.$(selector);
                    if (button) {{
                        const buttonText = await button.innerText();
                        log.info(`Found submit: "${{buttonText}}"`);
                        await button.click();
                        log.info(`✓ Clicked submit: ${{selector}}`);
                        submitClicked = true;
                        break;
                    }}
                }} catch (e) {{
                    // Try next
                }}
            }}
            
            if (!submitClicked) {{
                throw new Error('Could not find submit button');
            }}
            
            log.info('Waiting for navigation...');
            await page.waitForTimeout(6000);
            
            await page.screenshot({{ path: 'step4_after_login.png', fullPage: true }});
            
            const currentUrl = page.url();
            log.info(`Current URL: ${{currentUrl}}`);
            
            const isLoggedIn = !currentUrl.includes('login') && !currentUrl.includes('signin');
            
            if (isLoggedIn) {{
                log.info('✅ LOGIN SUCCESSFUL!');
                
                log.info('Navigating to search results...');
                await page.goto('{TARGET_URL}', {{ waitUntil: 'networkidle', timeout: 30000 }});
                await page.waitForTimeout(4000);
                log.info('✓ At search results page');
                
                log.info('=== SCRAPING DATA ===');
                
                if (page.url().includes('login')) {{
                    throw new Error('Redirected to login');
                }}
                
                await page.screenshot({{ path: 'step5_search_results.png', fullPage: true }});
                
                const tableSelectors = [
                    'table tbody tr',
                    '.ant-table-tbody tr',
                    '[class*="Table"] tbody tr',
                    'tbody tr'
                ];
                
                let rowsSelector = null;
                for (const selector of tableSelectors) {{
                    try {{
                        await page.waitForSelector(selector, {{ timeout: 5000 }});
                        const rowCount = await page.$$eval(selector, rows => rows.length);
                        log.info(`✓ Found ${{rowCount}} rows: ${{selector}}`);
                        rowsSelector = selector;
                        break;
                    }} catch (e) {{
                        log.info(`Not found: ${{selector}}`);
                    }}
                }}
                
                if (!rowsSelector) {{
                    const bodyText = await page.$eval('body', el => el.innerText).catch(() => 'Unable to read');
                    log.error('❌ No table found');
                    throw new Error('No results table found');
                }}
                
                const results = await page.$$eval(rowsSelector, (rows) => {{
                    return rows.map((row, idx) => {{
                        const cells = row.querySelectorAll('td');
                        if (cells.length === 0) return null;
                        
                        return {{
                            rowNumber: idx + 1,
                            companyName: cells[0]?.innerText?.trim() || '',
                            website: cells[1]?.querySelector('a')?.href || cells[0]?.querySelector('a')?.href || '',
                            industry: cells[2]?.innerText?.trim() || '',
                            location: cells[3]?.innerText?.trim() || '',
                            headcount: cells[4]?.innerText?.trim() || '',
                            email: cells[5]?.innerText?.trim() || (cells[5]?.querySelector('button') ? 'REVEAL_REQUIRED' : ''),
                            phone: cells[6]?.innerText?.trim() || (cells[6]?.querySelector('button') ? 'REVEAL_REQUIRED' : ''),
                            role: cells[7]?.innerText?.trim() || '',
                            cellCount: cells.length
                        }};
                    }}).filter(item => item !== null && item.companyName);
                }});
                
                log.info(`✅ Extracted ${{results.length}} records`);
                
                if (results.length > 0) {{
                    log.info('Sample: ' + JSON.stringify(results[0]));
                }}
                
                return {{
                    success: true,
                    results,
                    pageUrl: page.url(),
                    totalRecords: results.length,
                    scrapedAt: new Date().toISOString()
                }};
                
            }} else {{
                throw new Error('Login failed - still on login page');
            }}
            
        }} catch (error) {{
            log.error(`❌ ERROR: ${{error.message}}`);
            await page.screenshot({{ path: 'error_screenshot.png', fullPage: true }});
            throw error;
        }}
    }}
    
    return {{ url: request.url, title: await page.title() }};
}}""",
    "preNavigationHooks": """[
    async (crawlingContext, gotoOptions) => {
        const { page, log } = crawlingContext;
        
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        
        log.info('✓ Headers configured');
    }
]""",
    "postNavigationHooks": """[
    async (crawlingContext) => {
        const { page, log } = crawlingContext;
        
        await page.waitForTimeout(2000);
        
        if (page.url().includes('search/results') || page.url().includes('companies_search')) {
            try {
                log.info('Looking for reveal buttons...');
                
                const revealButtons = await page.$$('button:has-text("Reveal")');
                
                if (revealButtons.length > 0) {
                    log.info(`Found ${revealButtons.length} reveal buttons`);
                    
                    for (let i = 0; i < Math.min(revealButtons.length, 50); i++) {
                        try {
                            await revealButtons[i].click();
                            await page.waitForTimeout(300);
                        } catch (e) {
                            // Continue
                        }
                    }
                    
                    log.info('✓ Clicked reveal buttons');
                    await page.waitForTimeout(1500);
                }
            } catch (e) {
                log.info('Error with reveal buttons: ' + e.message);
            }
        }
        
        log.info('✓ Post-nav completed');
    }
]""",
    "proxyConfiguration": {
        "useApifyProxy": True,
        "apifyProxyGroups": ["RESIDENTIAL"]
    },
    "respectRobotsTxtFile": False,
    "startUrls": [
        {
            "url": "https://app.muraena.ai/login",
            "userData": {"label": "LOGIN"}
        }
    ],
    "useChrome": False,
    "waitUntil": "networkidle"
}


def run_scraper():
    """Run the Muraena.ai scraper"""
    print("🚀 Starting Muraena.ai scraper...")
    print(f"📍 Target URL: {TARGET_URL[:80]}...")
    
    try:
        # Run the Actor using Playwright Scraper
        print("📤 Sending scraper configuration to Apify...")
        run = client.actor("apify/playwright-scraper").call(run_input=run_input)
        
        print(f"✅ Actor run started: {run['id']}")
        print(f"🔗 View run: https://console.apify.com/actors/runs/{run['id']}")
        
        # Wait for the run to finish
        print("⏳ Waiting for scraper to complete...")
        
        # Get the run details
        run_client = client.run(run['id'])
        
        # Wait for completion (check every 10 seconds)
        while True:
            run_info = run_client.get()
            status = run_info['status']
            
            print(f"📊 Status: {status}")
            
            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break
            
            time.sleep(10)
        
        if status == 'SUCCEEDED':
            print("✅ Scraper completed successfully!")
            
            # Fetch results from the dataset
            print("📥 Fetching results...")
            dataset_id = run['defaultDatasetId']
            dataset_client = client.dataset(dataset_id)
            
            # Get all items from the dataset
            items = list(dataset_client.iterate_items())
            
            if items:
                print(f"\n📊 RESULTS: Found {len(items)} item(s)")
                
                # Save to JSON file
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
                                print(f"   {i+1}. {record.get('companyName', 'N/A')}")
                                print(f"      Industry: {record.get('industry', 'N/A')}")
                                print(f"      Location: {record.get('location', 'N/A')}")
                                print(f"      Email: {record.get('email', 'N/A')}")
                                print(f"      Phone: {record.get('phone', 'N/A')}")
                
                return items
            else:
                print("⚠️ No results found in dataset")
                return []
        
        else:
            print(f"❌ Scraper failed with status: {status}")
            
            # Get log
            print("\n📜 Fetching logs...")
            log_client = client.log(run['id'])
            log_content = log_client.get()
            
            # Save log to file
            log_file = 'scraper_error.log'
            with open(log_file, 'w') as f:
                f.write(log_content)
            
            print(f"📝 Error log saved to: {log_file}")
            print("\nLast 50 lines of log:")
            print("=" * 60)
            print('\n'.join(log_content.split('\n')[-50:]))
            
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def download_screenshots(run_id):
    """Download screenshots from the Apify run"""
    print(f"\n📸 Downloading screenshots from run: {run_id}")
    
    try:
        # Get key-value store
        run_info = client.run(run_id).get()
        kv_store_id = run_info['defaultKeyValueStoreId']
        kv_store = client.key_value_store(kv_store_id)
        
        # List of screenshot names to download
        screenshots = [
            'step1_email_filled.png',
            'step2_after_continue.png',
            'step3_before_submit.png',
            'step4_after_login.png',
            'step5_search_results.png',
            'error_screenshot.png'
        ]
        
        os.makedirs('screenshots', exist_ok=True)
        
        for screenshot in screenshots:
            try:
                record = kv_store.get_record(screenshot)
                if record and record['value']:
                    filepath = os.path.join('screenshots', screenshot)
                    with open(filepath, 'wb') as f:
                        f.write(record['value'])
                    print(f"✅ Downloaded: {screenshot}")
            except Exception as e:
                print(f"⚠️ Could not download {screenshot}: {str(e)}")
        
        print(f"📁 Screenshots saved to: screenshots/")
    
    except Exception as e:
        print(f"❌ Error downloading screenshots: {str(e)}")


if __name__ == "__main__":
    print("=" * 60)
    print("  MURAENA.AI SCRAPER - Python + Apify API")
    print("=" * 60)
    
    # Run the scraper
    results = run_scraper()
    
    if results:
        print("\n✅ Scraping completed successfully!")
        print(f"📊 Total results: {sum(len(item.get('results', [])) for item in results)}")
        
        # Optionally download screenshots
        # run_id = input("\nEnter run ID to download screenshots (or press Enter to skip): ").strip()
        # if run_id:
        #     download_screenshots(run_id)
    else:
        print("\n❌ Scraping failed. Check the logs above.")