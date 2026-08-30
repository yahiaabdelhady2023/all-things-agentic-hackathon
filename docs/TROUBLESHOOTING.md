# Troubleshooting Guide

Common issues and their solutions for the All Things Agentic system.

## 🚨 Google Authentication Issues

### Issue: "RefreshError: Token has been expired or revoked"

**What it means**: Your Google OAuth token is no longer valid

**Solution**:
1. The system automatically handles this
2. You'll be prompted to re-authenticate
3. Accept the browser login flow
4. New tokens will be saved

**If persists**:
```bash
# Delete expired token
rm google_services/gmail_token.json
# Run again - will prompt for login
uv run python3 main_file.py
```

---

### Issue: "The specified API key is invalid"

**What it means**: Credentials file is missing or corrupted

**Solution**:
1. Verify `credentials.json` exists in project root
2. If not, re-download from Google Cloud Console
3. Restart the application

```bash
# Check if file exists
ls -la credentials.json

# If missing, download from:
# https://console.cloud.google.com → Credentials → OAuth 2.0 Client ID
```

---

### Issue: "InvalidGrantError: The authorization code is invalid"

**What it means**: Authentication code was mistyped or expired

**Solution**:
1. Re-run the application
2. Accept browser authorization again
3. Copy code **carefully** (include entire string)
4. Paste into terminal with Ctrl+Shift+V

---

### Issue: "Access denied" or "Insufficient permissions"

**What it means**: Scopes not properly configured

**Solution**:
1. Go to Google Cloud Console
2. "APIs & Services" → "OAuth consent screen"
3. Click "EDIT APP"
4. Go to "Scopes"
5. Verify these 3 scopes present:
   - Gmail (readonly)
   - Drive (full access)
   - Calendar (full access)
6. Re-authenticate application

---

## 📧 Gmail Issues

### Issue: "No emails found"

**What it means**: No unread or recent emails in Gmail

**Causes**:
- Gmail is empty
- All emails are old
- API can't access Gmail

**Solutions**:
1. Send yourself a test email
2. Don't mark it as read
3. Run application again
4. Check Gmail API is enabled:
   ```bash
   # Should see "✓ Gmail API working"
   uv run python3 -c "from google_services.setup import build_service; build_service('gmail')"
   ```

---

### Issue: "Error downloading attachment"

**What it means**: Failed to download email attachment

**Solutions**:
1. Check attachment is not too large (>25MB)
2. Check disk space available
3. Check attachment type is supported (PDF, DOCX, etc.)
4. Check Gmail API permissions

---

### Issue: "Attachment not found locally"

**What it means**: Downloaded attachment is missing

**Solutions**:
1. Check `downloaded_emails/` folder exists
2. Check disk space
3. Re-download emails:
   ```bash
   rm -rf downloaded_emails/
   uv run python3 main_file.py
   ```

---

## 🗂️ Google Drive Issues

### Issue: "Drive folders are empty"

**What it means**: Folders created but no documents inside

**Solutions**:
1. Check documents exist on your Drive
2. Documents must match email requirements
3. Check document filenames:
   ```
   Email needs: "Passport"
   Drive file: "my_passport.pdf" ✓ (will match)
   Drive file: "travel_doc.pdf" ✗ (won't match)
   ```
4. Run Drive scanner to populate:
   ```bash
   uv run python3 main_file.py
   # Choose Drive Scanner option
   ```

---

### Issue: "Permission denied" on Drive operations

**What it means**: Application can't create folders/files on Drive

**Solutions**:
1. Check Drive API is enabled
2. Check OAuth scopes include Drive
3. Re-authenticate with proper permissions
4. Verify Drive account is accessible

---

### Issue: "File not found" or "Folder not found"

**What it means**: Referenced file/folder no longer exists

**Solutions**:
1. Don't manually delete URGENT_* folders during run
2. Check file IDs are valid
3. Refresh Drive cache:
   ```bash
   # Re-run scanner
   uv run python3 main_file.py
   ```

---

## 📅 Google Calendar Issues

### Issue: "Event not appearing in calendar"

**What it means**: Event created but not visible

**Solutions**:
1. Check calendar is visible in Google Calendar
2. Check event date is correct
3. Verify event was actually created:
   ```bash
   # Check logs for "✓ Event Created"
   uv run python3 main_file.py 2>&1 | grep -i calendar
   ```
4. Refresh Google Calendar app

---

### Issue: "Cannot create event" or "Event creation failed"

**What it means**: Calendar API error

**Solutions**:
1. Check Calendar API is enabled
2. Check you have write permissions to calendar
3. Check event date is valid (not in past)
4. Try with different deadline date

---

### Issue: "Calendar token expired"

**What it means**: Calendar authentication no longer valid

**Solutions**:
```bash
# Delete calendar token
rm google_services/calendar_token.json
# Re-run application
uv run python3 main_file.py
```

---

## 💾 Database Issues

### Issue: "Database locked" or "Database is corrupted"

**What it means**: SQLite database file is locked or damaged

**Solutions**:
1. Stop all running instances of the app
2. Try again (locks clear automatically)
3. If persists, backup and reset:
   ```bash
   # Backup database
   cp databases/emails.db databases/emails.db.backup
   # Reset database
   rm databases/emails.db
   uv run python3 main_file.py
   ```

---

### Issue: "Vector database error"

**What it means**: ChromaDB is not working

**Solutions**:
```bash
# Clear vector database
rm -rf databases/vector_db/
# Re-run application
uv run python3 main_file.py
```

---

## 💬 Chat Interface Issues

### Issue: "Chat doesn't find documents"

**What it means**: Vector search not working well

**Solutions**:
1. Use more specific keywords
2. Ask about specific emails instead
3. Re-index database:
   ```bash
   rm -rf databases/vector_db/
   uv run python3 main_file.py
   ```

---

### Issue: "Chat agent crashes"

**What it means**: Unexpected error in chat mode

**Solutions**:
1. Check database is not corrupted
2. Try restart
3. Check Python dependencies:
   ```bash
   uv sync
   ```

---

## 🔧 General Issues

### Issue: "ModuleNotFoundError: No module named..."

**What it means**: Missing Python dependency

**Solution**:
```bash
uv sync
uv run python3 main_file.py
```

---

### Issue: "Python version error"

**What it means**: Wrong Python version

**Solution**:
```bash
# Check version
python3 --version  # Should be 3.14+

# If not, uv handles it:
uv sync
uv run python3 main_file.py  # Uses correct version
```

---

### Issue: "Out of disk space"

**What it means**: Too many emails/attachments downloaded

**Solutions**:
1. Clean up old downloads:
   ```bash
   rm -rf downloaded_emails/
   ```
2. Clear database:
   ```bash
   rm databases/emails.db
   ```
3. Free up disk space on your system

---

### Issue: "Slow performance"

**What it means**: Application is taking too long

**Solutions**:
1. Too many emails to process
2. Slow internet connection
3. Large attachments being processed

**Optimizations**:
- Limit emails: Modify email scanner to get fewer emails
- Increase timeout values in code
- Process in batches instead of all at once

---

## 📊 Debug Mode

Enable verbose logging:

```bash
# Run with debug output
uv run python3 main_file.py 2>&1 | tee debug.log

# Search for errors
grep -i error debug.log

# Check specific agent
grep -i "Email Scanner" debug.log
grep -i "Calendar" debug.log
```

---

## 🆘 Getting Help

1. **Check logs**: All errors printed to terminal
2. **Re-authenticate**: Delete token files and re-run
3. **Reset databases**: Clear data and restart
4. **Check Google APIs**: Verify enabled in Cloud Console
5. **Review code**: Check `langgraph_module/` for agent logic

---

## 📋 Checklist

Before contacting support, verify:
- [ ] All Google APIs enabled (Gmail, Drive, Calendar)
- [ ] credentials.json in project root
- [ ] Python 3.14+ installed
- [ ] All dependencies installed (`uv sync`)
- [ ] Internet connection working
- [ ] Google account accessible
- [ ] Disk space available (>1GB)
- [ ] No other instance running

---

## 🎓 Common Fixes Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Token expired | `rm google_services/*_token.json && uv run python3 main_file.py` |
| Missing credentials | Download from Google Cloud Console |
| No emails found | Send test email to yourself |
| Empty Drive folders | Check document filenames match requirements |
| Chat not finding docs | Try more specific keywords |
| Slow performance | Clear downloads: `rm -rf downloaded_emails/` |
| Database error | Reset: `rm databases/emails.db` |
| Module not found | Install: `uv sync` |

---

**Last Updated**: August 2026  
**Need Help?** Check the main [README](README_COMPREHENSIVE.md)
