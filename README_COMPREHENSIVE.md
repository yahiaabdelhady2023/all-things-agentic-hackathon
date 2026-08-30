# 📧 All Things Agentic - Email & Document Automation

> **Automate your document management, email processing, and calendar scheduling with AI-powered agents**

A comprehensive agentic system that transforms how you handle emails, documents, and deadlines. This project integrates Gmail, Google Drive, and Google Calendar to automatically detect document requirements, organize files, and create reminders.

---

## 🎯 Problem Statement

Managing paperwork and documents is overwhelming:
- 📬 Dozens of emails with document requirements
- 📄 Critical documents scattered across Drive
- ⏰ Missed deadlines and lost reminders
- 🔄 Manual tracking of which documents are needed for what
- 😰 High stress from disorganized workflows

## ✨ Solution

An **autonomous multi-agent system** that:
- ✅ Automatically scans Gmail for emails requiring documents
- ✅ Detects which documents are needed for each email
- ✅ Creates organized Drive folders (e.g., `URGENT_Visa_Application`)
- ✅ Populates folders with relevant documents from Drive
- ✅ Creates calendar reminders for deadlines
- ✅ Provides a chat interface for questions about processed data

---

## 🏗️ Architecture Overview

The system consists of **5 main agents** working in orchestration:

```
Gmail Input
    ↓
[1. Email Scanner] → Scans emails, detects document requirements, downloads attachments
    ↓
[2. Calendar Scanner] → Extracts deadlines, creates calendar events
    ↓
[3. Drive Scanner] → Scans Drive, finds matching documents
    ↓
[4. Executor Agent] → Uploads attachments, populates folders with matching documents
    ↓
Google Drive (Organized) + Google Calendar (Reminders) + Chat Interface (Q&A)
```

---

## 🤖 Agent System Details

### 1. **Email Scanner Agent** 📧
**Purpose**: Core email processing engine

**Workflow**:
1. Scans Gmail for unread and recent emails
2. Downloads email attachments (PDF, DOCX, etc.)
3. Extracts text from documents for analysis
4. Detects required document types using regex patterns:
   - Passport, Driver License, Bank Statement, Visa
   - Birth Certificate, Identity Card, Proof of Address
   - Transcript, Resume, Insurance, and more
5. Creates Drive folders named `URGENT_[Email Subject]`
6. Uploads email attachments to corresponding folders

**Key Features**:
- Pattern-based document detection
- Automatic folder creation on Drive
- Email storage (local JSON + SQL database)
- Vector database indexing for semantic search
- Email attachment extraction

**Output State**:
```python
{
  "emails": [EmailData],
  "email_snippet_summary": str,
  "requires_documents": bool,
  "required_documents": [str],
  "drive_folder_id": str,
  "drive_folder_url": str
}
```

---

### 2. **Calendar Scanner Agent** 📅
**Purpose**: Deadline extraction and calendar management

**Workflow**:
1. Receives emails from Email Scanner
2. Extracts deadline hints from email content
3. Looks for action keywords (urgent, deadline, submit by, etc.)
4. Creates Google Calendar events with:
   - Event title (derived from email subject)
   - Date/time information
   - Description with email details
5. Stores event links for user reference

**Key Features**:
- Automatic deadline extraction
- Google Calendar integration
- Event tracking and persistence
- Backward-compatible database fallback

**Detected Keywords**:
- Urgent, deadline, submit, due date, expires, valid until
- Application deadline, registration closes, etc.

---

### 3. **Drive Scanner Agent** 🗂️
**Purpose**: Discover and catalog existing Drive documents

**Workflow**:
1. Reads all files from Google Drive
2. Filters for document files (PDF, DOCX, DOC, TXT, etc.)
3. **NEW**: Matches documents to email requirements
4. Adds matching documents as additional parents to email folders
5. Provides detailed logging of matches

**Key Features**:
- Full Drive content discovery
- Filename-based document matching
- Automatic folder population
- Content matching via email text analysis
- Error handling and detailed logging

---

### 4. **Executor Agent** ⚙️
**Purpose**: Task execution and automation

**Workflow**:
1. Receives tasks from other agents
2. Uploads email attachments to Drive folders
3. Scans Drive for documents matching email requirements
4. Adds relevant documents to email-specific folders
5. Logs all execution steps and errors

**Key Features**:
- Batch document operations
- Error recovery and logging
- WebViewLink generation for user access
- Comprehensive execution tracking

---

### 5. **Chat Agent** 💬 (Read-Only)
**Purpose**: User interaction and question answering

**Capabilities**:
- Answer questions about processed emails
- Provide document summaries
- Explain which documents are needed for what
- Reference calendar events and Drive folder links
- **NOTE**: Read-only mode (no API modifications)

**Supported Queries**:
- "What documents do I need for the visa?"
- "When is the deadline for X?"
- "Where are the documents for email Y?"
- "Summarize what was processed"

---

## 📊 Document Detection Patterns

The system recognizes 15+ document types:

| Category | Keywords |
|----------|----------|
| **Identity** | passport, driver license, identity card, national id |
| **Finance** | bank statement, credit card, financial proof |
| **Travel** | visa, travel permit, proof of address |
| **Education** | transcript, diploma, certificate, resume |
| **Insurance** | insurance policy, coverage proof |
| **Other** | birth certificate, marriage certificate |

---

## 🔄 Complete Workflow Example

### Scenario: Visa Application Email

**Step 1: Email Arrives**
```
From: visa@embassy.gov
Subject: Visa Application - Documents Required
Body: "Please submit passport, birth certificate, 
       bank statement, and employment letter"
```

**Step 2: Email Scanner Agent**
- ✅ Downloads email
- ✅ Detects required documents: `[passport, birth certificate, bank statement]`
- ✅ Creates Drive folder: `URGENT_Visa_Application`
- ✅ Uploads any attachments

**Step 3: Calendar Scanner Agent**
- ✅ Extracts deadline from email body
- ✅ Creates Google Calendar event
- ✅ Sets reminder for 3 days before deadline

**Step 4: Drive Scanner Agent**
- ✅ Scans all Drive files
- ✅ Finds: `my_passport.pdf`, `birth_cert.pdf`, `bank_statement.docx`
- ✅ Adds these files to `URGENT_Visa_Application` folder

**Step 5: User Sees**
- 📁 **Drive**: Organized folder with all required documents
- 📅 **Calendar**: Reminder for submission deadline
- 💬 **Chat**: Can ask "What's missing for my visa?"

---

## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- Google Account with:
  - Gmail enabled
  - Google Drive access
  - Google Calendar access
- Google Cloud Project with OAuth2 credentials

### Installation

```bash
# Clone the repository
cd all-things-agentic-hackathon

# Install dependencies using uv
uv sync

# Set up Google credentials
# 1. Download credentials.json from Google Cloud Console
# 2. Place in project root or google_services/ folder
```

### Running the Application

```bash
# Execute the complete workflow
uv run python3 main_file.py

# This will:
# 1. Scan your Gmail for emails needing documents
# 2. Create organized Drive folders
# 3. Add documents to folders
# 4. Create calendar reminders
# 5. Open interactive chat mode for questions
```

---

## 📁 Project Structure

```
all-things-agentic-hackathon/
├── main_file.py                      # Entry point - orchestrates all agents
├── README.md                         # Original README
├── README_COMPREHENSIVE.md           # This file
├── pyproject.toml                    # Project dependencies
├── credentials.json                  # Google OAuth credentials
├── *_token.json                      # OAuth tokens (auto-generated)
│
├── langgraph_module/                 # Agent implementations
│   ├── __init__.py
│   ├── email_scanner_agent.py        # Email scanning & document detection
│   ├── calender_scanner.py           # Deadline extraction & calendar events
│   ├── drive_scanner.py              # Drive content discovery
│   ├── executor_agent.py             # Task execution
│   ├── chat_agent.py                 # User Q&A interface
│   ├── planner_agent.py              # Task planning (optional)
│   └── extraction_tools.py           # PDF/DOCX text extraction
│
├── google_services/                  # Google API integrations
│   ├── __init__.py
│   ├── setup.py                      # OAuth2 authentication
│   ├── gmail.py                      # Gmail API wrapper
│   ├── drive.py                      # Drive API wrapper
│   ├── calender.py                   # Calendar API wrapper
│   ├── credentials.json              # OAuth config
│   └── *_token.json                  # Service tokens
│
├── databases/                        # Data persistence
│   ├── vector_db/                    # ChromaDB vector storage
│   └── emails.db                     # SQLite email storage
│
├── downloaded_emails/                # Local email cache
│   └── [email_id]/
│       ├── email_content.json        # Email metadata & body
│       └── attachments/              # Downloaded files
│
└── docs/                             # Documentation & diagrams
    ├── agent_diagrams/               # Visual agent workflows
    ├── API_SETUP.md                  # Google API configuration
    └── TROUBLESHOOTING.md            # Common issues & fixes
```

---

## 🔐 Authentication Flow

The system uses Google OAuth2 for secure access:

1. **First Run**: Automatic browser redirect to Google login
2. **Token Storage**: Tokens saved to `google_services/*_token.json`
3. **Auto-Refresh**: Tokens automatically refreshed when expired
4. **Re-authentication**: If token is invalid, user prompted to re-login

### Token Files Generated
- `google_services/gmail_token.json` → Gmail access
- `google_services/drive_token.json` → Drive access
- `google_services/calendar_token.json` → Calendar access

---

## 💾 Data Storage

### Local Storage
- **JSON**: Email metadata in `downloaded_emails/[id]/email_content.json`
- **Attachments**: Binary files in `downloaded_emails/[id]/attachments/`

### Database Storage
- **SQLite**: `databases/emails.db` - Email records & attachments
- **Vector DB**: `databases/vector_db/` - ChromaDB for semantic search

### Google Cloud
- **Drive**: Organized folders with documents
- **Calendar**: Event reminders
- **Gmail**: Original email source

---

## 🎨 Color-Coded Terminal Output

The application uses ANSI color codes for clarity:

```
✓ Success messages       → Green
⚠ Warnings             → Yellow
ℹ Info messages        → Cyan
📄 Documents needed    → Red/Bold
📅 Calendar events     → Cyan
🔍 Scanning operations → Various colors
```

---

## 🛠️ Configuration

### Email Scanner Settings
Edit `langgraph_module/email_scanner_agent.py`:
```python
DOCUMENT_PATTERNS = {
    'passport': r'passport',
    'driver_license': r'driver.*license|driving.*license',
    # ... more patterns
}
```

### Calendar Deadline Keywords
Edit `langgraph_module/calender_scanner.py`:
```python
ACTION_KEYWORDS = [
    'urgent', 'deadline', 'submit', 'due date',
    'expires', 'valid until', 'application deadline'
]
```

### Drive Folder Naming
Edit `langgraph_module/email_scanner_agent.py`:
```python
folder_name = f"URGENT_{email_title}"
```

---

## 📊 Supported Document Types

The system can detect and organize:

| Type | Examples |
|------|----------|
| Travel | Passport, Visa, Travel Permit |
| Identity | Driver License, National ID, Birth Certificate |
| Finance | Bank Statement, Credit Card, Proof of Income |
| Legal | Marriage Certificate, Power of Attorney |
| Education | Transcript, Diploma, Certificate, Resume |
| Insurance | Policy, Coverage Proof, Medical Records |

---

## 🐛 Troubleshooting

### "Token has been expired or revoked"
**Solution**: The system automatically detects expired tokens and prompts for re-authentication. Accept the browser redirect.

### "Drive folders are empty"
**Solution**: 
1. Ensure documents exist in your Drive root
2. Check document naming matches email requirements
3. Run scanner again - it uses content matching

### "Calendar events not appearing"
**Solution**:
1. Verify Google Calendar API is enabled
2. Check for `RefreshError` messages
3. Try re-authenticating

### "No emails found"
**Solution**:
1. Check Gmail has unread/recent emails
2. Verify Gmail API enabled
3. Ensure OAuth credentials have Gmail scope

---

## 🔄 Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 1: AUTOMATION                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Email Scanner Agent                                     │
│     ├── Scan Gmail                                          │
│     ├── Detect documents needed                             │
│     ├── Download attachments                                │
│     └── Create Drive folders                                │
│                      ↓                                       │
│  2. Calendar Scanner Agent                                  │
│     ├── Extract deadlines                                   │
│     └── Create calendar events                              │
│                      ↓                                       │
│  3. Drive Scanner Agent                                     │
│     ├── Find documents on Drive                             │
│     └── Match to email requirements                         │
│                      ↓                                       │
│  4. Executor Agent                                          │
│     ├── Upload email attachments                            │
│     └── Add Drive docs to folders                           │
│                      ↓                                       │
│              Output: Organized Drive & Calendar             │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    PHASE 2: INTERACTION                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Chat Interface (Read-Only)                                 │
│  ├── Answer questions about documents                       │
│  ├── Explain deadlines                                      │
│  ├── Reference Drive folders                                │
│  └── Provide summaries                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Performance & Scalability

- **Email Processing**: ~10-50 emails per run
- **Document Types**: 15+ patterns recognized
- **Drive Integration**: Scans thousands of files efficiently
- **Database**: SQLite + ChromaDB for fast lookups
- **API Calls**: Optimized with minimal redundancy

---

## 🤝 Contributing

This is a hackathon project. Contributions welcome:
- Add more document detection patterns
- Improve deadline extraction
- Enhance chat capabilities
- Add support for other cloud services

---

## 📝 License

Part of the "All Things Agentic" hackathon project.

---

## 👤 Author

**Yahia Abdelhady**  
Email: handyleaf11@gmail.com

---

## 🙏 Acknowledgments

- LangChain & LangGraph for agent orchestration
- Google APIs for seamless cloud integration
- ChromaDB for vector storage
- All contributors to open-source libraries

---

## 📞 Support

Having issues? Check:
1. [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common problems
2. [API_SETUP.md](docs/API_SETUP.md) - Google API configuration
3. Terminal output with debug information

---

**Last Updated**: August 2026  
**Version**: 0.1.0  
**Status**: Active Development
