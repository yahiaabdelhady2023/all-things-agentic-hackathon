from langgraph_module.email_scanner_agent import build_email_scanner_agent


graph = build_email_scanner_agent()
graph.invoke({})