from langchain_core.messages import HumanMessage

from langgraph_module.chat_agent import build_chat_agent
from langgraph_module.calender_scanner import build_calender_agent
from langgraph_module.drive_scanner import build_drive_scanner_agent
from langgraph_module.email_scanner_agent import build_email_scanner_agent
from langgraph_module.executor_agent import build_executor_agent

# ANSI Color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}➜ {text}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_docs_needed(sender, subject, required_docs, drive_url):
    print(f"{Colors.BOLD}{Colors.RED}📄 DOCUMENTS NEEDED{Colors.RESET}")
    print(f"   {Colors.YELLOW}From:{Colors.RESET} {sender}")
    print(f"   {Colors.YELLOW}Subject:{Colors.RESET} {subject}")
    print(f"   {Colors.YELLOW}Required:{Colors.RESET} {', '.join(required_docs)}")
    if drive_url:
        print(f"   {Colors.GREEN}Drive Folder:{Colors.RESET} {drive_url}")
    print()



def main():
    chat_graph = build_chat_agent()
    email_graph = build_email_scanner_agent()
    calendar_graph = build_calender_agent()
    drive_graph = build_drive_scanner_agent()
    executor_graph = build_executor_agent()
    
    # ===== PHASE 1: AUTOMATIC EMAIL PROCESSING =====
    print_header("AUTOMATIC EMAIL PROCESSING")
    
    print_section("Searching Gmail for unread and recent emails...")
    scan_result = email_graph.invoke({"target": None})  # Get all emails
    print_success(scan_result["email_snippet_summary"])
    print_info(f"Downloaded and indexed {len(scan_result['emails'])} email(s).")
    
    # Extract email info for document detection and Drive folder creation
    emails_with_docs = []
    for email in scan_result.get('emails', []):
        if email.requires_documents:
            emails_with_docs.append(email)
            print_docs_needed(email.sender, email.email_title, email.required_documents, email.drive_folder_url)
    
    print_success(f"Created {len(emails_with_docs)} document-related folder(s) on Drive.")

    print_section("Creating calendar reminders for urgent emails...")
    calendar_result = calendar_graph.invoke({"emails": scan_result.get('emails', [])})
    calendar_events = calendar_result.get("events", [])
    print_success(f"Created or found {len(calendar_events)} calendar reminder(s).")
    for event in calendar_events:
        print(f"   {Colors.CYAN}📅 {event.summary}{Colors.RESET}")
        if event.calendar_link:
            print(f"      {Colors.DIM}{event.calendar_link}{Colors.RESET}")

    print_section("Syncing Google Drive metadata...")
    drive_result = drive_graph.invoke({})
    print_success(f"Synced {len(drive_result['files'])} Drive item(s).")

    print_section("Planning and executing document tasks...")
    execution_result = executor_graph.invoke({})
    results = execution_result.get("execution_results", [])
    if not results:
        print_info("No document-related tasks were found.")
    for result in results:
        print(f"   {Colors.YELLOW}Status:{Colors.RESET} {result['status']}")
        if result.get('folder_url'):
            print(f"   {Colors.GREEN}Folder:{Colors.RESET} {result['folder_url']}")
    
    print_header("WORKFLOW COMPLETE")
    summary_data = [
        (f"Emails processed", len(scan_result.get('emails', []))),
        (f"Emails requiring documents", len(emails_with_docs)),
        (f"Calendar events created", len(calendar_events)),
        (f"Drive folders created", len(emails_with_docs)),
    ]
    for label, value in summary_data:
        print(f"{Colors.BOLD}{label:<35}{Colors.GREEN}{value}{Colors.RESET}")
    print()
    
    # ===== PHASE 2: INTERACTIVE CHAT ABOUT RESULTS =====
    print_header("INTERACTIVE CHAT MODE")
    print(f"{Colors.CYAN}Ask about your emails and tasks • Type 'quit' or 'exit' to end{Colors.RESET}\n")
    print_success("Emails and tasks are ready! What would you like to know?\n")
    
    chat_history = []
    
    while True:
        user_input = input(f"{Colors.BOLD}{Colors.BLUE}You:{Colors.RESET} ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            print(f"\n{Colors.GREEN}Agent: Goodbye!{Colors.RESET}")
            return

        chat_history.append(HumanMessage(content=user_input))
        chat_result = chat_graph.invoke({"messages": chat_history})
        chat_history = chat_result["messages"]
        print(f"\n{Colors.BOLD}{Colors.CYAN}Agent:{Colors.RESET} {chat_history[-1].content}\n")


if __name__ == "__main__":
    main()