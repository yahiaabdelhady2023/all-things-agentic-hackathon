```mermaid
graph TD
    A["📧 Email Input"] --> B["Extract Email Text"]
    B --> C["Search for<br/>Deadline Keywords"]
    C --> D{Found<br/>Deadline?}
    D -->|Yes| E["Parse Date/Time"]
    D -->|No| F["Use Default<br/>Deadline"]
    E --> G["Create Calendar<br/>Event Object"]
    F --> G
    G --> H["Set Event Title"]
    H --> I["Add Description<br/>with Email Details"]
    I --> J["Add Email Link &<br/>Drive Folder Link"]
    J --> K["Connect to<br/>Google Calendar API"]
    K --> L["Create Event"]
    L --> M["Save Event Link"]
    M --> N["Store in<br/>Database"]
    N --> O["✅ Event Created"]

    style A fill:#e1f5ff
    style O fill:#c8e6c9
    style D fill:#fff9c4
    style L fill:#f8bbd0
    style C fill:#ffe0b2
```

### Calendar Scanner Agent - Detailed Workflow

**Phase 1: Email Analysis**
- Receives email from Email Scanner
- Extracts full email text
- Searches for deadline indicators

**Phase 2: Deadline Extraction**
Recognizes keywords:
- "urgent", "deadline", "submit by"
- "due date", "expires", "valid until"
- "application closes", "registration deadline"

**Phase 3: Date/Time Parsing**
- Extracts specific dates if mentioned
- Uses defaults for missing dates
- Calculates relative dates ("2 weeks from now")

**Phase 4: Calendar Event Creation**
- Generates event object with:
  - Title: Email subject + document type
  - Date: Extracted deadline
  - Time: 9:00 AM (default)
  - Description: Email summary + requirements
  - Links: Email link + Drive folder

**Phase 5: Google Calendar Integration**
- Authenticates with Google Calendar API
- Creates event in primary calendar
- Returns event link and ID

**Phase 6: Persistence**
- Stores event record in SQLite
- Tracks event creation status
- Enables later reference in chat

**Output**: Calendar event data with:
- `summary`: Event title
- `start_date`: Event date
- `deadline_hint`: Extracted deadline
- `calendar_link`: Shareable event link
- `email_reference`: Link to original email
