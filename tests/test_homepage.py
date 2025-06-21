from playwright.sync_api import Page, expect

def test_homepage_loads(page: Page):
    """Test that the homepage loads successfully"""
    page.goto("/")
    expect(page).to_have_title("JobEas")
    
    # Check if the page has some basic content
    expect(page.locator("body")).to_be_visible()

def test_resume_builder_link(page: Page):
    """Test that the resume builder link works"""
    page.goto("/")
    
    # Look for resume builder link (adjust selector based on your actual HTML)
    resume_link = page.locator("a[href*='resume']").first
    if resume_link.is_visible():
        resume_link.click()
        expect(page).to_have_url(lambda url: "resume" in url)

def test_navigation_works(page: Page):
    """Test basic navigation functionality"""
    page.goto("/")
    
    # Test that we can navigate to different pages
    # This is a basic test - you'll need to adjust based on your actual navigation
    expect(page.locator("nav")).to_be_visible() 