#!/usr/bin/env python3
"""
Frontend Testing Script for Cover Letter Generation
Uses Playwright to simulate user interactions and test the cover letter generation flow.
"""

import asyncio
import os
from .base_test import BaseBrowserTest
from .test_config import (
    TEST_CONFIG, SELECTORS, URLS, SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME_TEXT,
    get_full_url, create_temp_resume_file, cleanup_temp_file
)

class CoverLetterFrontendTest(BaseBrowserTest):
    """Test class for cover letter frontend functionality."""
    
    async def test_method(self):
        """Main test method for cover letter generation."""
        print("🚀 Starting Cover Letter Generation Test...")
        
        # Navigate to the cover letter page
        print("📄 Navigating to cover letter page...")
        await self.navigate_to_page(URLS['cover_letter_page'])
        
        # Handle login if required - this will also navigate to cover letter page
        await self.handle_login()
        
        # Wait a moment for the page to fully load after navigation
        await self.page.wait_for_timeout(2000)
        
        # Log current page info
        await self.log_page_info()
        
        # Verify we're on the cover letter page before proceeding
        current_url = self.page.url
        if 'coverletter' not in current_url and 'job-cover-letter' not in current_url:
            print("❌ Not on cover letter page, attempting to navigate...")
            await self.navigate_to_page(URLS['cover_letter_page'])
            await self.page.wait_for_timeout(2000)
            await self.log_page_info()
        
        # Now start the actual cover letter tests
        print("🎯 Starting cover letter functionality tests...")
        
        # Test 1: Resume Selection (if available)
        await self.test_resume_selection()
        
        # Test 2: File Upload (if no resume selected)
        await self.test_file_upload()
        
        # Test 3: Job Description Input
        await self.test_job_description_input()
        
        # Test 4: Form Submission
        await self.test_form_submission()
        
        # Test 5: Results and Actions
        await self.test_results_and_actions()
        
        # Keep browser open for a moment to see results
        print("⏳ Keeping browser open for 5 seconds to view results...")
        await self.page.wait_for_timeout(5000)
    
    async def test_resume_selection(self):
        """Test resume selection functionality."""
        print("📋 Testing resume selection...")
        
        resume_cards = self.page.locator(SELECTORS['resume_selection']['cards'])
        if await resume_cards.count() > 0:
            print(f"   Found {await resume_cards.count()} resume(s)")
            # Click the first resume card
            await resume_cards.first.click()
            await self.page.wait_for_timeout(1000)  # Wait for selection
            print("   ✅ Resume selected successfully")
        else:
            print("   ⚠️ No resumes found, will test file upload")
    
    async def test_file_upload(self):
        """Test file upload functionality."""
        # Check if no resume is selected
        selected_resume = self.page.locator(SELECTORS['resume_selection']['selected'])
        if await selected_resume.count() == 0:
            print("📁 Testing file upload...")
            
            # Find file input
            file_input = await self.find_element(SELECTORS['file_upload']['input'])
            
            if file_input:
                print(f"   Found file input")
                
                # Create and upload temporary resume file
                temp_file = create_temp_resume_file(SAMPLE_RESUME_TEXT)
                try:
                    await file_input.set_input_files(temp_file)
                    await self.page.wait_for_timeout(1000)
                    print("   ✅ File uploaded successfully")
                finally:
                    cleanup_temp_file(temp_file)
            else:
                print("   ⚠️ No file input found, skipping file upload test")
    
    async def test_job_description_input(self):
        """Test job description input functionality."""
        print("💼 Testing job description input...")
        
        job_textarea = await self.find_element(SELECTORS['job_description']['textarea'])
        
        if job_textarea:
            await job_textarea.fill(SAMPLE_JOB_DESCRIPTION)
            print("   ✅ Job description entered successfully")
        else:
            print("   ❌ Job description textarea not found")
            # Take screenshot for debugging
            await self.take_screenshot('job_description_not_found.png')
            raise Exception("Job description textarea not found")
    
    async def test_form_submission(self):
        """Test form submission functionality."""
        print("🚀 Testing form submission...")
        
        submit_button = await self.find_element(SELECTORS['form_submission']['submit_button'])
        
        if submit_button:
            await submit_button.click()
            print("   ✅ Form submitted successfully")
            
            # Wait for AI processing
            await self.wait_for_ai_processing()
        else:
            print("   ❌ Submit button not found")
            await self.take_screenshot('submit_button_not_found.png')
            raise Exception("Submit button not found")
    
    async def test_results_and_actions(self):
        """Test results display and action buttons."""
        print("📄 Checking results...")
        
        # Find results section
        results_section = await self.find_element(SELECTORS['results']['section'])
        
        if results_section and await results_section.is_visible():
            print("   ✅ Results section is visible")
            
            # Check for cover letter content
            await self.test_cover_letter_content()
            
            # Test action buttons
            await self.test_action_buttons()
            
        else:
            print("   ❌ Results section not visible")
            
            # Check for errors
            error = await self.check_for_errors()
            if error:
                print(f"   ❌ {error}")
            else:
                print("   ❌ No results and no error messages found")
                await self.take_screenshot('no_results_found.png')
    
    async def test_cover_letter_content(self):
        """Test cover letter content generation."""
        print("   📝 Checking cover letter content...")
        
        content_element = await self.find_element(SELECTORS['results']['content'])
        
        if content_element:
            content = await content_element.text_content()
            if content and len(content.strip()) > 100:
                print(f"   ✅ Cover letter generated successfully ({len(content)} characters)")
                print(f"   📄 Preview: {content[:200]}...")
            else:
                print("   ❌ Cover letter content is empty or too short")
        else:
            print("   ❌ Cover letter content element not found")
    
    async def test_action_buttons(self):
        """Test action buttons functionality."""
        print("🔘 Testing action buttons...")
        
        # Test Copy Button
        copy_button = await self.find_element(SELECTORS['action_buttons']['copy'])
        if copy_button:
            await copy_button.click()
            print("   ✅ Copy button clicked")
        
        # Test Edit Button
        edit_button = await self.find_element(SELECTORS['action_buttons']['edit'])
        if edit_button:
            await edit_button.click()
            await self.page.wait_for_timeout(1000)
            print("   ✅ Edit button clicked")
        
        # Test Download Button
        download_button = await self.find_element(SELECTORS['action_buttons']['download'])
        if download_button:
            await download_button.click()
            print("   ✅ Download button clicked")
        
        # Test Email Button
        email_button = await self.find_element(SELECTORS['action_buttons']['email'])
        if email_button:
            await email_button.click()
            print("   ✅ Email button clicked")

async def test_backend_api():
    """Test the backend API directly using requests."""
    print("\n🔧 Testing Backend API...")
    
    try:
        import requests
        
        # Test data
        test_data = {
            'job_posting': SAMPLE_JOB_DESCRIPTION,
            'resume_text': SAMPLE_RESUME_TEXT
        }
        
        # Make a request to the cover letter generation endpoint
        url = get_full_url(URLS['cover_letter_page'])
        response = requests.post(url, data=test_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Backend API test successful")
                cover_letter = result.get('cover_letter', '')
                print(f"   📝 Generated cover letter length: {len(cover_letter)} characters")
                print(f"   📄 Preview: {cover_letter[:300]}...")
            else:
                print(f"   ❌ Backend API test failed: {result.get('error')}")
        else:
            print(f"   ❌ Backend API test failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Backend API test failed with error: {str(e)}")

async def main():
    """Main test function."""
    print("🧪 Starting Cover Letter Generation Tests\n")
    
    # Test backend first
    await test_backend_api()
    
    # Test frontend
    test = CoverLetterFrontendTest()
    await test.run_test("Cover Letter Frontend Test")
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 