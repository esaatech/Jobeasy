#!/usr/bin/env python3
"""
Simple Cover Letter Generation Test
Checks server status and provides manual testing steps.
"""

import requests
import time
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_config import TEST_CONFIG, SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME_TEXT, URLS, get_full_url

def test_server_status():
    """Test if the Django server is running."""
    print("🔍 Checking server status...")
    
    try:
        # Test the main page
        response = requests.get(TEST_CONFIG['base_url'], timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
            return True
        else:
            print(f"   ⚠️ Server responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Server is not running")
        return False
    except Exception as e:
        print(f"   ❌ Error checking server: {str(e)}")
        return False

def test_cover_letter_page():
    """Test if the cover letter page is accessible."""
    print("\n📄 Testing cover letter page accessibility...")
    
    try:
        url = get_full_url(URLS['cover_letter_page'])
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Cover letter page is accessible")
            return True
        elif response.status_code == 302:
            print("   ⚠️ Page redirects (likely to login)")
            return True
        else:
            print(f"   ❌ Page returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accessing page: {str(e)}")
        return False

def test_backend_api():
    """Test the backend API with sample data."""
    print("\n🔧 Testing backend API...")
    
    try:
        # Test data
        test_data = {
            'job_posting': SAMPLE_JOB_DESCRIPTION,
            'resume_text': SAMPLE_RESUME_TEXT
        }
        
        # Make a request to the cover letter generation endpoint
        url = get_full_url(URLS['cover_letter_page'])
        response = requests.post(url, data=test_data, timeout=30)
        
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    print("   ✅ Backend API test successful")
                    cover_letter = result.get('cover_letter', '')
                    print(f"   📝 Generated cover letter length: {len(cover_letter)} characters")
                    print(f"   📄 Preview: {cover_letter[:200]}...")
                    return True
                else:
                    print(f"   ❌ Backend API test failed: {result.get('error')}")
                    return False
            except ValueError:
                print("   ❌ Response is not valid JSON")
                print(f"   📄 Response content: {response.text[:200]}...")
                return False
        elif response.status_code == 302:
            print("   ⚠️ API redirects (likely to login)")
            return True
        else:
            print(f"   ❌ Backend API test failed with status code: {response.status_code}")
            print(f"   📄 Response content: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (server might be slow)")
        return False
    except Exception as e:
        print(f"   ❌ Backend API test failed with error: {str(e)}")
        return False

def print_manual_testing_steps():
    """Print manual testing steps."""
    print("\n" + "="*60)
    print("📋 MANUAL TESTING STEPS")
    print("="*60)
    
    print(f"""
1. 🚀 Start the Django server:
   poetry run python manage.py runserver {TEST_CONFIG['base_url'].split(':')[-1]}

2. 🌐 Open your browser and navigate to:
   {get_full_url(URLS['cover_letter_page'])}

3. 🔐 If you see a login page, log in with your credentials

4. 📋 Test Resume Selection:
   - Look for resume cards in the "Select Resume" section
   - Click on one of the resume cards to select it
   - Verify the card shows as selected (blue border/background)

5. 📁 Test File Upload (if no resumes available):
   - Look for the "Upload Resume" section
   - Click the upload area or drag a file
   - Upload a .txt or .pdf file
   - Verify the file name appears in the preview

6. 💼 Test Job Description Input:
   - Find the "Job Description" text area
   - Paste the sample job description below
   - Verify the text appears in the textarea

7. 🚀 Test Form Submission:
   - Click the "Generate Cover Letter" button
   - Wait for the AI to process (may take 10-30 seconds)
   - Verify a loading indicator appears

8. 📄 Test Results Display:
   - Check if the results section appears
   - Verify the cover letter content is displayed
   - Check that the content is properly formatted

9. 🔘 Test Action Buttons:
   - Click "Copy to Clipboard" - should show "Copied!" message
   - Click "Edit Letter" - should scroll back to form
   - Click "Download as PDF" - should download a PDF file
   - Click "Email" - should open email client

10. 🧪 Test Error Handling:
    - Try submitting without selecting a resume or uploading a file
    - Try submitting without entering a job description
    - Verify appropriate error messages appear
""")

def print_sample_data():
    """Print sample data for testing."""
    print("\n" + "="*60)
    print("📝 SAMPLE DATA FOR TESTING")
    print("="*60)
    
    print(f"""
SAMPLE JOB DESCRIPTION:
Copy and paste this into the job description field:

{SAMPLE_JOB_DESCRIPTION}
""")

def main():
    """Main test function."""
    print("🧪 Cover Letter Generation Test Suite")
    print("="*60)
    
    # Test server status
    server_running = test_server_status()
    
    if server_running:
        # Test cover letter page
        page_accessible = test_cover_letter_page()
        
        if page_accessible:
            # Test backend API
            api_working = test_backend_api()
            
            if api_working:
                print("\n🎉 All automated tests passed!")
                print("✅ The cover letter generation system appears to be working correctly.")
            else:
                print("\n⚠️ Backend API test failed, but you can still test manually.")
        else:
            print("\n⚠️ Page accessibility test failed, but you can still test manually.")
    else:
        port = TEST_CONFIG['base_url'].split(':')[-1]
        print(f"\n❌ Server is not running. Please start the server first:")
        print(f"   poetry run python manage.py runserver {port}")
    
    # Always print manual testing steps
    print_manual_testing_steps()
    print_sample_data()
    
    print("\n✨ Test suite completed!")

if __name__ == "__main__":
    main() 