from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import TypedDict, List, Literal
from pydantic import BaseModel, Field
from typing import Optional, Annotated
import operator
from PIL import Image
import io

class State(TypedDict):
    msg: Annotated[list[str], operator.add]


def node_a(state: State):
    return {"msg":["hi from node a"]}

def node_b(state: State):
    return {"msg":["hi from node b"]}


graph = StateGraph(State)
graph.add_node("node_a",node_a)
graph.add_node("node_b",node_b)
graph.add_edge(START,"node_a")
graph.add_edge("node_a","node_b")
graph.add_edge("node_b",END)
graph = graph.compile()
bytes_graph = graph.get_graph().draw_mermaid_png()
io_bytes_graph = io.BytesIO(bytes_graph)
img = Image.open(io_bytes_graph)
img.show("hello")
result=graph.invoke({})
print(result)