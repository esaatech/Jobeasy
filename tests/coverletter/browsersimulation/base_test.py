"""
Base test class for Cover Letter Browser Simulation Tests
Provides common functionality and utilities for all browser tests.
"""

import asyncio
import os
from playwright.async_api import async_playwright
from .test_config import TEST_CONFIG, SELECTORS, URLS, get_full_url

class BaseBrowserTest:
    """Base class for browser simulation tests."""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None
    
    async def setup(self):
        """Setup browser and page for testing."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=TEST_CONFIG['headless']
        )
        self.page = await self.browser.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(TEST_CONFIG['timeout'])
    
    async def teardown(self):
        """Cleanup browser and page."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate_to_page(self, url_path):
        """Navigate to a specific page."""
        full_url = get_full_url(url_path)
        await self.page.goto(full_url)
        await self.page.wait_for_load_state('networkidle')
    
    async def handle_login(self):
        """Handle login if required."""
        if await self.page.locator(SELECTORS['login']['username']).count() > 0:
            print("🔐 Login required, waiting for manual login...")
            print("   Please enter your credentials in the browser window.")
            
            try:
                # Wait for login to complete and redirect
                await self.page.wait_for_function("""
                    () => {
                        // Check if we're no longer on login page
                        const loginForm = document.querySelector('input[name="username"]');
                        if (loginForm) return false;
                        
                        // Check if we're on any authenticated page
                        return !window.location.pathname.includes('login');
                    }
                """, timeout=60000)
                
                print("   ✅ Login appears to be successful")
                await self.page.wait_for_timeout(2000)
                
                # Log current page info
                await self.log_page_info()
                
                # Try to click the Cover Letter navigation link
                print("   🔄 Looking for Cover Letter navigation link...")
                cover_letter_link = await self.find_element(SELECTORS['navigation']['cover_letter_link'])
                
                if cover_letter_link:
                    print("   🔗 Found Cover Letter link, clicking...")
                    await cover_letter_link.click()
                    await self.page.wait_for_load_state('networkidle')
                    print("   ✅ Clicked Cover Letter link")
                    await self.log_page_info()
                else:
                    print("   ⚠️ Cover Letter link not found, navigating directly...")
                    await self.navigate_to_page(URLS['cover_letter_page'])
                
            except Exception as e:
                print(f"   ❌ Login timeout or error: {str(e)}")
                print("   Please login manually and then press Enter to continue...")
                input()
                
                # Try to click the Cover Letter navigation link
                print("   🔄 Looking for Cover Letter navigation link...")
                cover_letter_link = await self.find_element(SELECTORS['navigation']['cover_letter_link'])
                
                if cover_letter_link:
                    print("   🔗 Found Cover Letter link, clicking...")
                    await cover_letter_link.click()
                    await self.page.wait_for_load_state('networkidle')
                    print("   ✅ Clicked Cover Letter link")
                    await self.log_page_info()
                else:
                    print("   ⚠️ Cover Letter link not found, navigating directly...")
                    await self.navigate_to_page(URLS['cover_letter_page'])
    
    async def find_element(self, selectors, timeout=5000):
        """Find an element using multiple selectors."""
        for selector in selectors:
            try:
                element = self.page.locator(selector)
                await element.wait_for(timeout=timeout)
                return element
            except Exception:
                continue
        return None
    
    async def wait_for_element(self, selectors, timeout=5000):
        """Wait for an element to appear using multiple selectors."""
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout)
                return True
            except Exception:
                continue
        return False
    
    async def take_screenshot(self, filename='test_screenshot.png'):
        """Take a screenshot for debugging."""
        try:
            await self.page.screenshot(path=filename)
            print(f"📸 Screenshot saved as '{filename}'")
            return filename
        except Exception as e:
            print(f"❌ Failed to take screenshot: {str(e)}")
            return None
    
    async def get_page_content(self):
        """Get the current page content for debugging."""
        try:
            return await self.page.content()
        except Exception:
            return "Unable to get page content"
    
    async def log_page_info(self):
        """Log current page information for debugging."""
        try:
            title = await self.page.title()
            url = self.page.url
            print(f"📄 Current page: {title} ({url})")
        except Exception as e:
            print(f"❌ Unable to get page info: {str(e)}")
    
    async def wait_for_ai_processing(self, timeout=None):
        """Wait for AI processing to complete."""
        if timeout is None:
            timeout = TEST_CONFIG['wait_timeout']
        
        print(f"   ⏳ Waiting for AI processing ({timeout/1000}s)...")
        await self.page.wait_for_timeout(timeout)
    
    async def check_for_errors(self):
        """Check for error messages on the page."""
        for selector in SELECTORS['error_messages']:
            if await self.page.locator(selector).count() > 0:
                error_text = await self.page.locator(selector).first.text_content()
                return f"Error found: {error_text}"
        return None
    
    async def run_test(self, test_name):
        """Run a test with proper setup and teardown."""
        print(f"🧪 Running test: {test_name}")
        
        try:
            await self.setup()
            await self.test_method()
            print(f"✅ Test '{test_name}' completed successfully")
            
        except Exception as e:
            print(f"❌ Test '{test_name}' failed: {str(e)}")
            if TEST_CONFIG['screenshot_on_error']:
                await self.take_screenshot(f"{test_name}_error.png")
            raise
            
        finally:
            await self.teardown()
    
    async def test_method(self):
        """Override this method in subclasses to implement specific tests."""
        raise NotImplementedError("Subclasses must implement test_method()") 