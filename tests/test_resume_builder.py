from playwright.sync_api import Page, expect
import time

def test_resume_builder_page_loads(page: Page):
    """Test that the resume builder page loads successfully"""
    page.goto("/resume/")
    expect(page).to_have_title(lambda title: "resume" in title.lower())
    
    # Check for key elements on the resume builder page
    expect(page.locator("h1")).to_contain_text("Resume")

def test_create_new_resume_flow(page: Page):
    """Test the complete flow of creating a new resume"""
    page.goto("/resume/")
    
    # Look for create new resume button
    create_button = page.locator("button:has-text('Create New Resume')").first
    if create_button.is_visible():
        create_button.click()
        
        # Wait for the form to load
        page.wait_for_selector("form", timeout=5000)
        
        # Fill in personal information
        page.fill("input[name='fullName']", "John Doe")
        page.fill("input[name='title']", "Software Engineer")
        page.fill("input[name='email']", "john.doe@example.com")
        page.fill("input[name='phone']", "123-456-7890")
        page.fill("textarea[name='summary']", "Experienced software engineer with 5+ years of experience.")
        
        # Submit the form
        submit_button = page.locator("button[type='submit']").first
        if submit_button.is_visible():
            submit_button.click()
            
            # Wait for success message or redirect
            page.wait_for_timeout(2000)

def test_resume_optimization_flow(page: Page):
    """Test the resume optimization functionality"""
    page.goto("/resume/optimize/")
    
    # Check if the optimization page loads
    expect(page.locator("h1")).to_contain_text("Optimize")
    
    # Test file upload (if available)
    file_input = page.locator("input[type='file']").first
    if file_input.is_visible():
        # Note: You'll need to provide a test PDF file
        # file_input.set_input_files("path/to/test-resume.pdf")
        pass
    
    # Test text input
    text_area = page.locator("textarea[name='resume_text']").first
    if text_area.is_visible():
        text_area.fill("Sample resume content for testing")
    
    # Test job description input
    job_desc = page.locator("textarea[name='job_description']").first
    if job_desc.is_visible():
        job_desc.fill("Software Engineer position requiring Python, Django, and JavaScript")

def test_template_selection(page: Page):
    """Test template selection functionality"""
    page.goto("/resume/")
    
    # Look for template selection options
    template_options = page.locator("[data-template]")
    if template_options.count() > 0:
        # Click on a template option
        template_options.first.click()
        
        # Verify template preview or selection
        page.wait_for_timeout(1000)

def test_resume_download(page: Page):
    """Test resume download functionality"""
    page.goto("/resume/download/")
    
    # Look for download buttons
    download_buttons = page.locator("button:has-text('Download')")
    if download_buttons.count() > 0:
        # Test PDF download
        pdf_button = page.locator("button:has-text('PDF')").first
        if pdf_button.is_visible():
            # Note: This will trigger a download, which Playwright handles
            pdf_button.click()
            page.wait_for_timeout(2000)

def test_responsive_design(page: Page):
    """Test that the resume builder is responsive"""
    page.goto("/resume/")
    
    # Test mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    expect(page.locator("body")).to_be_visible()
    
    # Test tablet viewport
    page.set_viewport_size({"width": 768, "height": 1024})
    expect(page.locator("body")).to_be_visible()
    
    # Test desktop viewport
    page.set_viewport_size({"width": 1920, "height": 1080})
    expect(page.locator("body")).to_be_visible() 