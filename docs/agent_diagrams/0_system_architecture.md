```mermaid
graph TB
    subgraph "Data Sources"
        GMAIL["📧 Google Gmail<br/>Emails & Attachments"]
        DRIVE["🗂️ Google Drive<br/>Existing Documents"]
        CALENDAR["📅 Google Calendar<br/>Events & Deadlines"]
    end
    
    subgraph "Agent System"
        ESA["🤖 Email Scanner<br/>Agent"]
        CSA["🤖 Calendar Scanner<br/>Agent"]
        DSA["🤖 Drive Scanner<br/>Agent"]
        EXA["🤖 Executor<br/>Agent"]
        CHA["🤖 Chat Agent<br/>Interactive Q&A"]
    end
    
    subgraph "Processing Pipeline"
        EXTRACT["📄 Extract & Parse<br/>Content Analysis"]
        DETECT["🔍 Document Detection<br/>Pattern Matching"]
        ORGANIZE["📁 Folder Creation<br/>Structure Building"]
        POPULATE["📤 Document Population<br/>File Organization"]
        TRACK["💾 Data Persistence<br/>Database Storage"]
    end
    
    subgraph "Data Storage"
        SQL["💾 SQLite Database<br/>Email Records"]
        VDB["🔍 ChromaDB<br/>Vector Search"]
        LOCAL["📂 Local Cache<br/>Downloaded Files"]
    end
    
    subgraph "Outputs"
        OUT_DRIVE["✅ Organized Drive<br/>URGENT_* Folders"]
        OUT_CAL["✅ Calendar Events<br/>Deadlines & Reminders"]
        OUT_CHAT["✅ Chat Interface<br/>Q&A System"]
    end
    
    GMAIL --> ESA
    GMAIL --> CSA
    DRIVE --> DSA
    CALENDAR --> CSA
    
    ESA --> EXTRACT
    CSA --> EXTRACT
    DSA --> EXTRACT
    
    EXTRACT --> DETECT
    DETECT --> ORGANIZE
    ORGANIZE --> POPULATE
    POPULATE --> TRACK
    
    EXTRACT -.-> VDB
    TRACK --> SQL
    TRACK --> LOCAL
    
    POPULATE --> EXA
    EXA --> OUT_DRIVE
    EXA --> OUT_CAL
    
    SQL --> CHA
    VDB --> CHA
    LOCAL --> CHA
    OUT_DRIVE --> CHA
    OUT_CAL --> CHA
    
    CHA --> OUT_CHAT
    
    style ESA fill:#ffccbc
    style CSA fill:#fff9c4
    style DSA fill:#b3e5fc
    style EXA fill:#f8bbd0
    style CHA fill:#c8e6c9
    style EXTRACT fill:#e0f2f1
    style DETECT fill:#e0f2f1
    style ORGANIZE fill:#e0f2f1
    style POPULATE fill:#e0f2f1
    style OUT_DRIVE fill:#c8e6c9
    style OUT_CAL fill:#c8e6c9
    style OUT_CHAT fill:#c8e6c9
```

## System Architecture Overview

This diagram shows the complete data flow through the system:

**Data Flow Stages**:

1. **Input Stage**: Data from Gmail, Drive, and Calendar
2. **Agent Stage**: Five specialized agents process data
3. **Processing Pipeline**: Extract → Detect → Organize → Populate → Track
4. **Storage Stage**: SQLite, Vector DB, and local cache
5. **Output Stage**: Organized Drive, Calendar events, Chat interface

**Key Flows**:
- Primary flow (solid lines): Main data processing path
- Secondary flow (dotted lines): Vector indexing for chat search
- Feedback loops: Agents cross-reference each other's results

See individual agent diagrams for detailed workflows.
