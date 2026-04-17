# Gmail OAuth Setup Guide

This guide explains how to set up Gmail OAuth for combined login and email sending functionality in JobEas.

## Environment Variables Required

Create a `.env` file in the project root with the following variables:

```env
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
# Must match the address you use in the browser (scheme, host, port, path, trailing slash).
# Example for local ASGI (common): port 8010
GOOGLE_REDIRECT_URI=http://127.0.0.1:8010/email/auth/gmail/callback/
```

**Important:** Register the **exact** same URI under Google Cloud Console → Credentials → your OAuth client → Authorized redirect URIs. If `.env` says port `8010` but Google only lists `8009`, token exchange will fail after you approve consent. `127.0.0.1` and `localhost` are different hosts for matching purposes—use one consistently.

While the app is in **Testing** on the OAuth consent screen, only **test users** you add there can complete sensitive scopes (e.g. Gmail send). Add your Google account as a test user or complete Google verification for production.

## Google Cloud Console Setup

### 1. Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Gmail API

### 2. Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required information:
   - App name: "JobEas"
   - User support email: your email
   - Developer contact information: your email
4. Add scopes:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/gmail.send`

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs (must mirror `GOOGLE_REDIRECT_URI` exactly):
   - `http://127.0.0.1:8010/email/auth/gmail/callback/` (example local ASGI)
   - `http://localhost:8010/email/auth/gmail/callback/` (add both localhost and 127.0.0.1 only if you use both)
   - `https://yourdomain.com/email/auth/gmail/callback/` (for production)
5. Copy the Client ID and Client Secret to your `.env` file

## Features Implemented

### 1. Combined Login and Email Sending
- Users can login with their Gmail account
- New users are automatically created with their Gmail profile
- Existing users can connect their Gmail for email sending
- Gmail authentication is automatically created for new Gmail users

### 2. OAuth Flow
- **Login Flow**: New users → Account creation → Gmail connection
- **Connect Flow**: Existing users → Gmail connection only
- **Email Sending**: Uses stored Gmail credentials to send emails

### 3. User Experience
- "Continue with Gmail" button on login page
- Automatic redirect back to original page after OAuth
- Success/error messages for all operations
- Gmail settings page to manage connection

## API Endpoints

- `GET /email/auth/gmail/` - Start OAuth flow
- `GET /email/auth/gmail/callback/` - Handle OAuth callback
- `GET /email/compose/<type>/<id>/` - Email composition page
- `POST /email/send/` - Send email via Gmail API
- `GET /email/history/` - View sent emails
- `GET /email/settings/` - Gmail connection settings
- `POST /email/disconnect/` - Disconnect Gmail

## Security Features

- OAuth state verification
- Token refresh handling
- Secure credential storage
- CSRF protection
- Session-based redirect handling

## Testing

1. Start the development server (use the same port as in `GOOGLE_REDIRECT_URI`):
   ```bash
   poetry run uvicorn jobeas.asgi:application --reload --host 0.0.0.0 --port 8010
   ```

2. Visit the login page and click "Continue with Gmail"

3. Complete the OAuth flow

4. Test email sending from resume or cover letter pages

## Production Deployment

For production, update the `GOOGLE_REDIRECT_URI` in your environment variables to match your domain:

```env
GOOGLE_REDIRECT_URI=https://yourdomain.com/email/auth/gmail/callback/
```

Also update the redirect URI in Google Cloud Console to include your production domain. 