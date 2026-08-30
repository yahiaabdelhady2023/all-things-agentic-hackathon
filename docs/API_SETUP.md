# Google API Setup Guide

This guide walks you through setting up Google APIs for the All Things Agentic system.

## 📋 Prerequisites

- Google Account
- Google Cloud Console access
- Administrator access to your Google account

## 🔧 Step 1: Create a Google Cloud Project

### 1.1 Go to Google Cloud Console
1. Visit https://console.cloud.google.com
2. Sign in with your Google account
3. Click on the project dropdown (top left)
4. Click "NEW PROJECT"
5. Enter project name: `AllThingsAgentic`
6. Leave organization blank (or select if in organization)
7. Click "CREATE"
8. Wait for project to be created (1-2 minutes)

### 1.2 Select Your Project
1. Once created, click on the project name in the dropdown
2. You should see your project ID (something like `allthingsagentic-12345`)

## 🔐 Step 2: Enable Required APIs

### 2.1 Enable Gmail API
1. In Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on the result
4. Click "ENABLE"
5. Wait for it to finish

### 2.2 Enable Google Drive API
1. Go back to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on the result
4. Click "ENABLE"
5. Wait for it to finish

### 2.3 Enable Google Calendar API
1. Go back to "APIs & Services" → "Library"
2. Search for "Google Calendar API"
3. Click on the result
4. Click "ENABLE"
5. Wait for it to finish

**You should now have 3 APIs enabled** ✓

## 🔑 Step 3: Create OAuth 2.0 Credentials

### 3.1 Create OAuth Consent Screen
1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" for User Type
3. Click "CREATE"
4. Fill in the form:
   - **App name**: `All Things Agentic`
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click "SAVE AND CONTINUE"
6. On "Scopes" page, click "ADD OR REMOVE SCOPES"
7. Search for and add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/calendar`
8. Click "UPDATE"
9. Click "SAVE AND CONTINUE"
10. Click "SAVE AND CONTINUE" again (skip adding test users)
11. Click "BACK TO DASHBOARD"

### 3.2 Create Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "CREATE CREDENTIALS" → "OAuth client ID"
3. Select "Desktop application" for Application type
4. Enter name: `AllThingsAgentic-Desktop`
5. Click "CREATE"
6. You'll see a popup with Client ID and Secret
   - **IMPORTANT**: Keep this information safe!
   - You'll need it in the next step

## 📥 Step 4: Download and Configure Credentials

### 4.1 Download JSON File
1. In the Credentials page, find your OAuth client ID
2. Click the download button (looks like ⬇️)
3. Save as `credentials.json`

### 4.2 Place File in Project
1. Copy the `credentials.json` file
2. Paste into your project root directory:
   ```
   all-things-agentic-hackathon/
   ├── credentials.json  ← Here
   ├── main_file.py
   ├── pyproject.toml
   ...
   ```

**Alternative location** (google_services folder):
   ```
   all-things-agentic-hackathon/
   ├── google_services/
   │   ├── credentials.json  ← Or here
   │   ...
   ```

## ✅ Step 5: First Run & Authentication

### 5.1 Run the Application
```bash
cd /home/yahia/code_projects/all-things-agentic-hackathon
uv run python3 main_file.py
```

### 5.2 Authorize Access
1. A browser window will open automatically
2. You'll see "Google hasn't verified this app"
3. Click "Continue" (or "Advanced" → "Go to...")
4. Review the permissions requested:
   - Read your emails
   - View and manage Drive files
   - View and edit Calendar
5. Click "Allow"
6. Copy the authorization code shown
7. Paste into the terminal prompt
8. Press Enter

### 5.3 Token Saved
The system will create token files:
- `google_services/gmail_token.json`
- `google_services/drive_token.json`
- `google_services/calendar_token.json`

**Keep these files safe!** They grant access to your Google account.

## 🔄 Token Refresh

Tokens automatically refresh when:
- They expire (every 7 days)
- The system detects they're invalid
- On application startup

If you see "Token expired" error:
1. The system will automatically prompt for re-authentication
2. Follow the browser OAuth flow again
3. New tokens will be saved

## 🚨 Troubleshooting

### "Invalid Credentials Error"
**Solution**:
1. Delete all `*_token.json` files
2. Delete `credentials.json`
3. Re-download from Google Cloud Console
4. Run application again to re-authenticate

### "API Not Enabled Error"
**Solution**:
1. Go to Cloud Console
2. Go to "APIs & Services" → "Library"
3. Make sure all 3 APIs are ENABLED:
   - Gmail API ✓
   - Google Drive API ✓
   - Google Calendar API ✓

### "Access Denied / Insufficient Permissions"
**Solution**:
1. Delete token files
2. Re-authenticate with proper scopes
3. Ensure OAuth scopes include all 3 services

### "RefreshError: Token has been expired or revoked"
**Solution**:
1. Normal - system handles this automatically
2. If persists, delete token file and re-authenticate
3. Check if you revoked app access in Google Account

## 🔒 Security Best Practices

### DO:
- ✅ Keep `credentials.json` in project root
- ✅ Keep `*_token.json` files safe
- ✅ Don't commit to public repositories
- ✅ Regenerate credentials if compromised

### DON'T:
- ❌ Share credential files with others
- ❌ Commit to GitHub without .gitignore
- ❌ Post credentials in issues/forums
- ❌ Use service account keys for personal use

### .gitignore Setup
Add to `.gitignore`:
```
credentials.json
*_token.json
gmail_token.json
drive_token.json
calendar_token.json
```

## 📊 Verify Setup

Run this command to verify everything works:
```bash
uv run python3 -c "
from google_services.setup import build_service
try:
    gmail = build_service('gmail')
    print('✓ Gmail API working')
    drive = build_service('drive')
    print('✓ Drive API working')
    calendar = build_service('calendar')
    print('✓ Calendar API working')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## 🎓 Next Steps

1. ✅ APIs enabled and credentials configured
2. ✅ Tokens saved automatically on first run
3. Ready to use the application!
4. See [README_COMPREHENSIVE.md](../README_COMPREHENSIVE.md) for usage

## 📞 Support

If issues persist:
1. Check Google Cloud Console for API status
2. Verify OAuth scopes in consent screen
3. Check application logs for detailed errors
4. Review the [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Last Updated**: August 2026  
**Status**: Google Cloud API Setup Complete
