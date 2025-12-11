"""
Cookie Extraction Helper for Muraena.ai

This script helps you extract cookies after manual login.
It opens a browser where you can login, then automatically extracts cookies.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python extract_cookies.py
"""

import json
import asyncio
from playwright.async_api import async_playwright


async def extract_cookies():
    """
    Opens a browser for manual login and extracts cookies afterward.
    """
    print("=" * 60)
    print("  MURAENA.AI COOKIE EXTRACTION HELPER")
    print("=" * 60)
    print()
    print("📋 Instructions:")
    print("1. A browser window will open")
    print("2. Login to Muraena.ai manually:")
    print("   - Enter your email")
    print("   - Check your email for the magic link")
    print("   - Click the magic link")
    print("3. Once logged in, come back to this terminal")
    print("4. Press ENTER to extract cookies")
    print()
    print("⚠️  Do NOT close the browser window until cookies are extracted!")
    print("=" * 60)
    print()
    
    input("Press ENTER to open the browser...")
    
    async with async_playwright() as p:
        # Launch browser (not headless so you can see it)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to Muraena.ai login page
        print("🌐 Opening Muraena.ai login page...")
        await page.goto('https://app.muraena.ai/login')
        
        print("✋ Now login manually in the browser window...")
        print("   (Check your email for the magic link)")
        print()
        
        # Wait for user to complete login
        input("⏸️  Press ENTER after you've successfully logged in...")
        
        # Get current URL to verify login
        current_url = page.url
        print(f"📍 Current URL: {current_url}")
        
        if 'login' in current_url or 'signin' in current_url:
            print("⚠️  WARNING: You might still be on the login page!")
            print("   Make sure you clicked the magic link in your email.")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                await browser.close()
                return
        
        # Extract cookies
        print("🍪 Extracting cookies...")
        cookies = await context.cookies()
        
        if not cookies:
            print("❌ No cookies found!")
            await browser.close()
            return
        
        print(f"✅ Found {len(cookies)} cookies")
        
        # Filter for important cookies (auth-related)
        important_keywords = ['session', 'auth', 'token', 'user', 'login', 'muraena']
        important_cookies = [
            cookie for cookie in cookies
            if any(keyword in cookie['name'].lower() for keyword in important_keywords)
        ]
        
        if important_cookies:
            print(f"🔑 Found {len(important_cookies)} authentication-related cookies:")
            for cookie in important_cookies:
                print(f"   - {cookie['name']}")
        else:
            print("⚠️  No obvious auth cookies found, will save all cookies")
            important_cookies = cookies
        
        # Format cookies for Python
        python_cookies = []
        for cookie in important_cookies:
            python_cookie = {
                "name": cookie['name'],
                "value": cookie['value'],
                "domain": cookie['domain'],
                "path": cookie['path'],
                "httpOnly": cookie.get('httpOnly', False),
                "secure": cookie.get('secure', False)
            }
            python_cookies.append(python_cookie)
        
        # Save to file
        output_file = 'extracted_cookies.json'
        with open(output_file, 'w') as f:
            json.dump(python_cookies, f, indent=2)
        
        print(f"\n💾 Cookies saved to: {output_file}")
        
        # Also save Python-formatted version
        python_file = 'extracted_cookies.py'
        with open(python_file, 'w') as f:
            f.write("# Extracted cookies for Muraena.ai\n")
            f.write("# Copy the COOKIES list below to your scraper script\n\n")
            f.write("COOKIES = ")
            f.write(json.dumps(python_cookies, indent=4))
        
        print(f"🐍 Python format saved to: {python_file}")
        
        # Display cookies
        print("\n📋 COPY THIS TO YOUR SCRAPER:")
        print("=" * 60)
        print("COOKIES = [")
        for i, cookie in enumerate(python_cookies):
            print("    {")
            print(f'        "name": "{cookie["name"]}",')
            print(f'        "value": "{cookie["value"]}",')
            print(f'        "domain": "{cookie["domain"]}",')
            print(f'        "path": "{cookie["path"]}",')
            print(f'        "httpOnly": {cookie["httpOnly"]},')
            print(f'        "secure": {cookie["secure"]}')
            if i < len(python_cookies) - 1:
                print("    },")
            else:
                print("    }")
        print("]")
        print("=" * 60)
        
        print("\n✅ Done! You can close the browser now.")
        print("\n📝 Next steps:")
        print("1. Copy the COOKIES list above")
        print("2. Paste it into 'muraena_scraper_cookies.py'")
        print("3. Run: python muraena_scraper_cookies.py")
        
        # Wait before closing
        input("\nPress ENTER to close the browser and exit...")
        await browser.close()


async def main():
    """Main function"""
    try:
        await extract_cookies()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if playwright is installed
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ ERROR: Playwright is not installed")
        print("\nPlease install it with:")
        print("  pip install playwright")
        print("  playwright install chromium")
        exit(1)
    
    # Run the extraction
    asyncio.run(main())