# Agent Diagrams Documentation

Welcome to the visual documentation of the All Things Agentic system!

## 📊 Available Diagrams

This folder contains detailed Mermaid diagrams for each agent and the overall system architecture.

### System Level

- **[System Architecture](0_system_architecture.md)** 🏗️
  - Complete data flow overview
  - Shows how all agents work together
  - Illustrates input → processing → output

### Individual Agents

1. **[Email Scanner Agent](1_email_scanner_agent.md)** 📧
   - Gmail scanning and document detection
   - Attachment extraction and analysis
   - Drive folder creation workflow
   - Database storage operations

2. **[Calendar Scanner Agent](2_calendar_scanner_agent.md)** 📅
   - Deadline extraction from emails
   - Google Calendar event creation
   - Event tracking and persistence

3. **[Drive Scanner Agent](3_drive_scanner_agent.md)** 🗂️
   - Drive file discovery
   - Document type identification
   - Matching documents to email requirements
   - Folder population process

4. **[Executor Agent](4_executor_agent.md)** ⚙️
   - Task execution orchestration
   - Attachment upload operations
   - Document matching and linking
   - Error handling and reporting

5. **[Chat Agent](5_chat_agent.md)** 💬
   - User query processing
   - Database and vector search
   - Response generation with links
   - Interactive session management

## 🎨 Diagram Format

All diagrams use **Mermaid** flowchart syntax:
- **Colors**: Different colors for different operations
- **Shapes**: 
  - Rectangles: Process steps
  - Diamonds: Decision points
  - Rounded boxes: Start/End points
- **Arrows**: Show process flow direction

## 📖 How to Use These Diagrams

### For Understanding the System
1. Start with [System Architecture](0_system_architecture.md) to see the big picture
2. Then explore individual agent diagrams to understand each component
3. Follow the flowchart arrows to understand the process step-by-step

### For Implementation
- Use diagrams to understand error handling requirements
- Reference to understand API calls needed
- Check for parallel vs. sequential processing

### For Debugging
- Trace through the diagram to find where issues might occur
- Identify which agent handles which operation
- Understand data passing between agents

## 🔄 Process Summary

```
User Email
    ↓
Email Scanner: Analyze & Extract
    ↓
Calendar Scanner: Find Deadlines
    ↓
Drive Scanner: Find Matching Docs
    ↓
Executor: Upload & Organize
    ↓
Results: Drive Folders + Calendar + Chat
    ↓
User: Ask Questions via Chat Agent
```

## 💡 Key Takeaways

- **Agents work in sequence**: Each agent's output becomes input for the next
- **Parallel processing**: Some operations (like Drive scanning) are efficient
- **Data persistence**: All information stored for later chat queries
- **User-friendly**: Final chat interface provides easy access to all processed data

## 🛠️ For Developers

### Adding a New Agent
1. Create new diagram: `X_agent_name.md`
2. Follow the same format
3. Show inputs, processes, decisions, and outputs
4. Include examples where relevant

### Modifying Existing Agents
1. Update the corresponding diagram
2. Ensure all new steps are shown
3. Update decision trees if logic changes
4. Add new output fields to the summary

### Viewing Diagrams
Diagrams render in:
- GitHub (automatic Mermaid support)
- VS Code with Mermaid extension
- Online Mermaid editor: https://mermaid.live

## 📞 Questions?

Refer to the main [README](../README_COMPREHENSIVE.md) for:
- Installation instructions
- Configuration details
- Troubleshooting guide
- API setup requirements
