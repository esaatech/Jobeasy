// Cookie Consent Management
class CookieConsent {
    constructor() {
        this.cookieName = 'jobeas_cookie_consent';
        this.bannerElement = document.getElementById('cookie-banner');
        this.init();
    }

    init() {
        // Check if user has already made a choice
        if (!this.hasUserConsented()) {
            this.showBanner();
        }
    }

    hasUserConsented() {
        return localStorage.getItem(this.cookieName) !== null;
    }

    showBanner() {
        if (this.bannerElement) {
            // Wait a bit for page load, then show banner
            setTimeout(() => {
                this.bannerElement.classList.remove('translate-y-full');
            }, 1000);
        }
    }

    hideBanner() {
        if (this.bannerElement) {
            this.bannerElement.classList.add('translate-y-full');
        }
    }

    acceptCookies() {
        localStorage.setItem(this.cookieName, 'accepted');
        this.hideBanner();
        this.enableAnalytics();
        console.log('Cookies accepted');
    }

    declineCookies() {
        localStorage.setItem(this.cookieName, 'declined');
        this.hideBanner();
        this.disableAnalytics();
        console.log('Cookies declined');
    }

    enableAnalytics() {
        // Enable Google Analytics or other tracking scripts
        // This is where you would initialize your analytics
        console.log('Analytics enabled');
    }

    disableAnalytics() {
        // Disable analytics tracking
        // This is where you would disable analytics
        console.log('Analytics disabled');
    }

    getUserPreference() {
        return localStorage.getItem(this.cookieName);
    }

    resetConsent() {
        localStorage.removeItem(this.cookieName);
        this.showBanner();
    }
}

// Global functions for button onclick handlers
function acceptCookies() {
    if (window.cookieConsent) {
        window.cookieConsent.acceptCookies();
    }
}

function declineCookies() {
    if (window.cookieConsent) {
        window.cookieConsent.declineCookies();
    }
}

// Initialize cookie consent when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.cookieConsent = new CookieConsent();
}); 