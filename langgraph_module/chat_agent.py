from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

################################################################
# 1. Model Configuration                                        #
################################################################

# Fixed model name to a valid Gemini model
llm = init_chat_model(model="gemini-3.5-flash"", model_provider="google_genai")

################################################################
# 2. State                                                      #
################################################################

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_request: str
    email_query: str
    start_task: bool

################################################################
# 3. Validation Models                                          #
################################################################

class UserRequest_Schema(BaseModel):
    user_request: str = Field(description="Given the messages, what is the user's specific target or goal?")
    email_query: str = Field(description="Convert the request into a concise Gmail search query. Remove conversational filler such as find, search, look for, emails about, related to, and please. Keep the meaningful topic words. Use Gmail operators such as from:, subject:, has:attachment, after:, before: when appropriate. Do not include explanations or quotes around the whole query.")

class StartTask_Schema(BaseModel):
    start_task: bool = Field(description="Return True if the user's request is completely clear and actionable, False otherwise.")

################################################################
# 4. Nodes                                                      #
################################################################

def analyze_task_status(state: State):
    """Node 1: Evaluates if we have enough information to start."""
    schema_llm = llm.with_structured_output(StartTask_Schema)
    
    # .invoke() returns the Pydantic object, so we access the attribute using .start_task
    result = schema_llm.invoke(state["messages"])
    
    return {"start_task": result.start_task}

def ask_question(state: State):
    """Node 2: Asks the user for more clarification."""
    instructions = "Given this history, ask a question to understand the user's task (related to paperwork/traveling)."
    
    # Best practice: SystemMessage should go at the beginning of the list
    messages_to_pass = [SystemMessage(content=instructions)] + state["messages"]
    message = llm.invoke(messages_to_pass)
    
    return {"messages": [message]}

def extract_task(state: State):
    """Extract the user's goal and the Gmail query the scanner should run."""
    instructions = SystemMessage(content=(
        "Extract the email search request from this conversation. Return a concise Gmail query "
        "that searches the user's intended topic. Remove filler such as 'find emails about' and "
        "keep the meaningful terms. For example, turn 'find visa paperwork emails' into "
        "'visa paperwork', and preserve explicit constraints such as sender, subject, date, or "
        "attachments. If the request is broad but actionable, keep the broad topic. Return only "
        "structured fields."
    ))
    schema_llm = llm.with_structured_output(UserRequest_Schema)
    result = schema_llm.invoke([instructions] + state["messages"])
    
    return {
        "messages": [AIMessage(content="STARTING TASK!...................")],
        "user_request": result.user_request,
        "email_query": result.email_query,
    }

################################################################
# 5. Router and Graph Build                                     #
################################################################

def route_task(state: State):
    # Route based on the boolean we set in analyze_task_status
    if state.get("start_task") == True:
        return "extract_task"
    return "ask_question"

def build_chat_agent():
    graph = StateGraph(State)
    
    graph.add_node("analyze_task_status", analyze_task_status)
    graph.add_node("ask_question", ask_question)
    graph.add_node("extract_task", extract_task)

    # 1. Start by analyzing the current state
    graph.add_edge(START, "analyze_task_status")
    
    # 2. Route based on the analysis
    graph.add_conditional_edges(
        "analyze_task_status", 
        route_task,
        {"extract_task": "extract_task", "ask_question": "ask_question"}
    )
    
    # 3. Both paths end the turn so the while loop can ask for human input
    graph.add_edge("ask_question", END)
    graph.add_edge("extract_task", END)
    
    return graph.compile()

graph = build_chat_agent()