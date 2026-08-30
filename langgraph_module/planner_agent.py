import os
import sqlite3
from typing import Optional, TypedDict

import chromadb
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class TaskModel(BaseModel):
    task_id: str
    email_id: str
    title: str
    description: str
    required_documents: list[str] = Field(default_factory=list)
    status: str = "planned"


class EmailModel(BaseModel):
    email_id: str
    email_title: str
    email_body: str
    sender: str = ""


class DriveFileModel(BaseModel):
    file_id: str
    name: str
    mime_type: str
    web_view_link: Optional[str] = None
    parent_path: str = ""


class State(TypedDict, total=False):
    tasks: list[TaskModel]
    emails: list[EmailModel]
    drive_files: list[DriveFileModel]
    semantic_context: dict[str, str]


def _database_path():
    return os.path.join("databases", "email_database.db")


def _load_database_rows():
    if not os.path.exists(_database_path()):
        return [], []
    connection = sqlite3.connect(_database_path())
    emails = connection.execute(
        "SELECT message_id, email_title, email_body, sender FROM emails"
    ).fetchall()
    drive_files = connection.execute(
        "SELECT file_id, name, mime_type, web_view_link, parent_path FROM drive_files"
    ).fetchall()
    connection.close()
    return emails, drive_files


def load_planning_context(state: State):
    email_rows, drive_rows = _load_database_rows()
    return {
        "emails": [EmailModel(email_id=row[0], email_title=row[1] or "", email_body=row[2] or "", sender=row[3] or "") for row in email_rows],
        "drive_files": [DriveFileModel(file_id=row[0], name=row[1], mime_type=row[2], web_view_link=row[3], parent_path=row[4] or "") for row in drive_rows],
    }


def _document_names(text):
    known_documents = [
        "passport", "identity", "id card", "driver license", "driving licence",
        "bank statement", "proof of address", "visa", "birth certificate",
        "transcript", "certificate", "resume", "cv", "tax", "insurance",
    ]
    lowered = text.lower()
    return [name for name in known_documents if name in lowered]


def analysize_all_emails(state: State):
    tasks = []
    for email in state.get("emails", []):
        text = f"{email.email_title}\n{email.email_body}"
        required_documents = _document_names(text)
        if not required_documents:
            continue
        task_id = f"task_{email.email_id}"
        tasks.append(TaskModel(
            task_id=task_id,
            email_id=email.email_id,
            title=email.email_title or "Email paperwork task",
            description=email.email_body[:1000],
            required_documents=required_documents,
        ))
    return {"tasks": tasks}


def get_drive_filenames(state: State):
    return {"drive_files": state.get("drive_files", [])}


def get_vector_context(state: State):
    context = {}
    try:
        collection = chromadb.PersistentClient(path="databases/vector_db").get_collection(
            name="email_and_attachments"
        )
        for email in state.get("emails", []):
            if email.email_body and collection.count():
                result = collection.query(query_texts=[email.email_body[:1000]], n_results=3)
                context[email.email_id] = "\n".join(result.get("documents", [[]])[0])
    except Exception:
        context = {}
    return {"semantic_context": context}


def plan_tasks(state: State):
    """Match requested document names against the indexed Drive metadata."""
    drive_files = state.get("drive_files", [])
    planned_tasks = []
    for task in state.get("tasks", []):
        matches = [
            file.name for file in drive_files
            if any(document in file.name.lower() for document in task.required_documents)
        ]
        description = task.description
        semantic_context = state.get("semantic_context", {}).get(task.email_id)
        if semantic_context:
            description += f"\nRelated indexed context: {semantic_context[:1000]}"
        if matches:
            description += f"\nMatching Drive files: {', '.join(matches)}"
        planned_tasks.append(task.model_copy(update={"description": description}))
    return {"tasks": planned_tasks}


def build_planner_agent():
    graph = StateGraph(State)
    graph.add_node("load_planning_context", load_planning_context)
    graph.add_node("analysize_all_emails", analysize_all_emails)
    graph.add_node("get_drive_filenames", get_drive_filenames)
    graph.add_node("get_vector_context", get_vector_context)
    graph.add_node("plan_tasks", plan_tasks)
    graph.add_edge(START, "load_planning_context")
    graph.add_edge("load_planning_context", "analysize_all_emails")
    graph.add_edge("analysize_all_emails", "get_drive_filenames")
    graph.add_edge("get_drive_filenames", "get_vector_context")
    graph.add_edge("get_vector_context", "plan_tasks")
    graph.add_edge("plan_tasks", END)
    return graph.compile()