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
llm = init_chat_model(model="gemini-2.5-flash", model_provider="google_genai")

################################################################
# 2. State                                                      #
################################################################

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_request: str
    start_task: bool

################################################################
# 3. Validation Models                                          #
################################################################

class UserRequest_Schema(BaseModel):
    user_request: str = Field(description="Given the messages, what is the user's specific target or goal?")

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
    """Node 3: Extracts the final task and notifies the user."""
    schema_llm = llm.with_structured_output(UserRequest_Schema)
    result = schema_llm.invoke(state["messages"])
    
    return {
        "messages": [AIMessage(content="STARTING TASK!...................")],
        "user_request": result.user_request # Accessing the Pydantic attribute
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

################################################################
# 6. External Chat Loop                                         #
################################################################

# Keep track of the history outside the graph
chat_history = []
start_task = False

print("Agent: Hello! I can help you plan your travel or paperwork. What do you need?")

while not start_task:
    user_input = input("\nYou: ")
    
    # Convert input to a HumanMessage and add it to our running history
    chat_history.append(HumanMessage(content=user_input))
    
    # Pass the ENTIRE history into the graph so it remembers context
    result = graph.invoke({"messages": chat_history})
    
    # Print the latest AI response
    latest_ai_msg = result["messages"][-1].content
    print(f"Agent: {latest_ai_msg}")
    
    # Update our variables for the next loop
    chat_history = result["messages"]
    start_task = result.get("start_task", False)

print("\n--- FINAL RESULT ---")
print(f"Extracted Goal: {result.get('user_request')}")