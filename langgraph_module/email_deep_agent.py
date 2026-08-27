import os
import json
from typing import TypedDict, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import operator
from PIL import Image
import io
from datetime import datetime



