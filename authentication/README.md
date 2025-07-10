# Jobeas Authentication App

This Django app provides robust, user-friendly authentication for your project, including registration, login, logout, and password reset. It is designed for easy reuse across multiple Django projects and features modern UI/UX and strong security practices.

---

## Features
- **User Registration** (Sign Up)
- **User Login** (Sign In) with username/email (case-insensitive)
- **Logout**
- **Password Reset** (email-based)
- **Password Change** (after login)
- **Session Management** ("Remember me" support)
- **Branded, Responsive UI** (with logo, password visibility toggle, and mobile-friendly design)
- **Debug Tools** (development only)

---

## Authentication Workflow

### 1. **Registration (Sign Up)**
- **URL:** `/auth/register/`
- **Form:** Username, Email, Password, Confirm Password
- **Process:**
  - User submits registration form
  - User is created and logged in automatically
  - Welcome email is sent (if configured)
  - Redirects to dashboard or resume creation

### 2. **Login (Sign In)**
- **URL:** `/auth/login/`
- **Form:** Username or Email, Password, Remember Me
- **Process:**
  - User submits login form
  - Authenticates with username (case-insensitive) or email (case-insensitive)
  - On success: user is logged in, session is set (persistent if "Remember me" checked)
  - On failure: error message is shown
  - Redirects to dashboard or next page

### 3. **Logout**
- **URL:** `/auth/logout/`
- **Process:**
  - User is logged out and redirected to home

### 4. **Password Reset**
- **Request Reset:** `/auth/password-reset/`
- **Email Sent:** `/auth/password-reset/done/`
- **Set New Password:** `/auth/password-reset-confirm/<uidb64>/<token>/`
- **Complete:** `/auth/password-reset-complete/`
- **Process:**
  - User requests reset with email
  - Receives email with reset link
  - Sets new password via secure form

### 5. **Debug Authentication (Development Only)**
- **URL:** `/auth/debug-auth/`
- **Purpose:** Test and debug authentication issues (only visible if `DEBUG=True`)

---

## Forms & UI/UX
- **Modern, responsive design** using Tailwind CSS
- **Password visibility toggle** (eye icon) for all password fields
- **Branded with Jobeas logo** (visible on all devices)
- **Clear error messages** and validation
- **Mobile-friendly**: illustration is hidden on mobile, logo always shown
- **Vertical spacing** between fields for clarity

---

## Endpoints (URLs)
| URL | Name | Description |
|-----|------|-------------|
| `/auth/login/` | `authentication:login` | Login page |
| `/auth/register/` | `authentication:register` | Registration page |
| `/auth/logout/` | `authentication:logout` | Logout endpoint |
| `/auth/password-reset/` | `authentication:password_reset` | Request password reset |
| `/auth/password-reset/done/` | `authentication:password_reset_done` | Reset email sent |
| `/auth/password-reset-confirm/<uidb64>/<token>/` | `authentication:password_reset_confirm` | Set new password |
| `/auth/password-reset-complete/` | `authentication:password_reset_complete` | Reset complete |
| `/auth/debug-auth/` | `authentication:debug_auth` | Debug tool (dev only) |

---

## How Authentication Works
- **Case-insensitive login:** Users can log in with any case variation of their username or email.
- **Whitespace handling:** Leading/trailing spaces are trimmed from input.
- **Session expiry:** If "Remember me" is unchecked, session expires on browser close.
- **Security:** Passwords are never logged or exposed.
- **Welcome email:** Sent on registration (if email backend is configured).

---

## Changelog & Recent Improvements

### 2024-07
- **Case-insensitive authentication:**
  - Users can log in with any case variation of their username or email.
  - Fixed device/browser-specific login issues.
- **Whitespace handling:**
  - Trims spaces from username/email fields to prevent login errors.
- **Password visibility toggle:**
  - Added eye icon to all password fields (login, signup, password reset).
  - Users can show/hide passwords for better UX.
- **Branded UI:**
  - Jobeas logo added above forms (always visible, even on mobile).
- **Improved spacing:**
  - Added vertical spacing between input fields for a cleaner look.
- **Debug tools:**
  - `/auth/debug-auth/` for troubleshooting authentication (dev only).
- **Production-safe logging:**
  - File logging only enabled in development; console logging in production.
- **Security:**
  - Debug tools and sensitive info only available in development mode.

---

## Usage in Other Projects
- Copy the `authentication` app into your Django project.
- Add `'authentication'` to `INSTALLED_APPS` in your `settings.py`.
- Include the authentication URLs in your main `urls.py`:
  ```python
  path('auth/', include('authentication.urls', namespace='authentication')),
  ```
- Ensure you have email backend configured for password reset and welcome emails.
- Place your logo at `static/img/logo.png` (or update the path in the templates).

---

## Customization
- **Logo:** Replace `static/img/logo.png` with your own branding.
- **Email templates:** Edit templates in `authentication/templates/authentication/` for custom messaging.
- **UI:** Tweak Tailwind classes in the templates for your preferred look.
- **Debug tools:** Remove or restrict `/auth/debug-auth/` in production.

---

## License
MIT (or your project license) 