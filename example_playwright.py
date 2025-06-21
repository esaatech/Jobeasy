#!/usr/bin/env python3
"""
Example Playwright script for web automation
This demonstrates basic Playwright usage with your Django application
"""
from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to True for headless mode
        page = browser.new_page()
        
        try:
            # Navigate to your Django application
            print("Navigating to Django application...")
            page.goto("http://localhost:8000/")
            
            # Wait for page to load
            page.wait_for_load_state("networkidle")
            
            # Take a screenshot
            page.screenshot(path="homepage.png")
            print("Screenshot saved as homepage.png")
            
            # Check page title
            title = page.title()
            print(f"Page title: {title}")
            
            # Look for specific elements
            h1_elements = page.locator("h1")
            if h1_elements.count() > 0:
                print(f"Found {h1_elements.count()} h1 elements")
                for i in range(h1_elements.count()):
                    text = h1_elements.nth(i).text_content()
                    print(f"  H1 {i+1}: {text}")
            
            # Test navigation to resume builder
            print("\nTesting resume builder navigation...")
            resume_links = page.locator("a[href*='resume']")
            if resume_links.count() > 0:
                print("Found resume link, clicking...")
                resume_links.first.click()
                page.wait_for_load_state("networkidle")
                
                # Take screenshot of resume page
                page.screenshot(path="resume_page.png")
                print("Resume page screenshot saved as resume_page.png")
                
                # Check if we're on the resume page
                current_url = page.url
                print(f"Current URL: {current_url}")
            
            # Test form interactions (if forms exist)
            print("\nTesting form interactions...")
            forms = page.locator("form")
            if forms.count() > 0:
                print(f"Found {forms.count()} forms")
                
                # Look for input fields
                inputs = page.locator("input[type='text'], input[type='email'], textarea")
                if inputs.count() > 0:
                    print(f"Found {inputs.count()} input fields")
                    
                    # Fill in the first text input (if it exists)
                    text_inputs = page.locator("input[type='text']")
                    if text_inputs.count() > 0:
                        text_inputs.first.fill("Test User")
                        print("Filled in test data")
            
            # Test responsive design
            print("\nTesting responsive design...")
            viewports = [
                {"width": 375, "height": 667, "name": "Mobile"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 1920, "height": 1080, "name": "Desktop"}
            ]
            
            for viewport in viewports:
                page.set_viewport_size(viewport)
                page.screenshot(path=f"responsive_{viewport['name'].lower()}.png")
                print(f"Screenshot saved for {viewport['name']} viewport")
                time.sleep(1)
            
            print("\nPlaywright automation completed successfully!")
            
        except Exception as e:
            print(f"Error during automation: {e}")
            page.screenshot(path="error_screenshot.png")
            print("Error screenshot saved as error_screenshot.png")
        
        finally:
            # Close browser
            browser.close()

if __name__ == "__main__":
    main() 