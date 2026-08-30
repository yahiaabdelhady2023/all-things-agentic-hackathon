from langchain_core.messages import HumanMessage

from langgraph_module.chat_agent import build_chat_agent
from langgraph_module.calender_scanner import build_calender_agent
from langgraph_module.drive_scanner import build_drive_scanner_agent
from langgraph_module.email_scanner_agent import build_email_scanner_agent
from langgraph_module.executor_agent import build_executor_agent


def main():
    chat_graph = build_chat_agent()
    email_graph = build_email_scanner_agent()
    calendar_graph = build_calender_agent()
    drive_graph = build_drive_scanner_agent()
    executor_graph = build_executor_agent()
    chat_history = []

    print("Agent: What emails should I find?")
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            return

        chat_history.append(HumanMessage(content=user_input))
        chat_result = chat_graph.invoke({"messages": chat_history})
        chat_history = chat_result["messages"]
        print(f"Agent: {chat_history[-1].content}")

        if not chat_result.get("start_task"):
            continue

        email_query = chat_result["email_query"]
        print(f"Searching Gmail with: {email_query}")
        scan_result = email_graph.invoke({"target": email_query})
        print(scan_result["email_snippet_summary"])
        print(f"Downloaded and indexed {len(scan_result['emails'])} email(s).")

        print("Creating calendar reminders for important emails...")
        calendar_result = calendar_graph.invoke({})
        calendar_events = calendar_result.get("events", [])
        print(f"Created or found {len(calendar_events)} calendar reminder(s).")
        for event in calendar_events:
            print(f"Calendar event: {event.summary} - {event.calendar_link or 'link unavailable'}")

        print("Syncing Google Drive metadata...")
        drive_result = drive_graph.invoke({})
        print(f"Synced {len(drive_result['files'])} Drive item(s).")

        print("Planning and executing document tasks...")
        execution_result = executor_graph.invoke({})
        results = execution_result.get("execution_results", [])
        if not results:
            print("No document-related tasks were found.")
        for result in results:
            print(f"Task status: {result['status']}")
            print(f"Task folder: {result['folder_url']}")
        return


if __name__ == "__main__":
    main()