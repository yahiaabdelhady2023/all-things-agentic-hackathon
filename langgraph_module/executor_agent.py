import mimetypes
import os
import re
import sqlite3
import tempfile
from typing import TypedDict

from google_services.drive import create_drive_file, create_drive_folder, download_drive_file
from langgraph.graph import END, START, StateGraph

from .planner_agent import (
    TaskModel,
    analysize_all_emails,
    get_drive_filenames,
    get_vector_context,
    load_planning_context,
    plan_tasks,
)


class ExecutorState(TypedDict, total=False):
    tasks: list[TaskModel]
    emails: list
    drive_files: list
    execution_results: list[dict]


def _database_path():
    return os.path.join("databases", "email_database.db")


def _open_execution_database():
    os.makedirs("databases", exist_ok=True)
    connection = sqlite3.connect(_database_path())
    connection.execute("""
        CREATE TABLE IF NOT EXISTS executed_tasks (
            task_id TEXT PRIMARY KEY,
            email_id TEXT NOT NULL,
            folder_id TEXT NOT NULL,
            folder_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return connection


def _email_attachments(email_id):
    attachment_folder = os.path.join("downloaded_emails", str(email_id), "attachments")
    if not os.path.isdir(attachment_folder):
        return []
    return [
        os.path.join(attachment_folder, filename)
        for filename in os.listdir(attachment_folder)
        if os.path.isfile(os.path.join(attachment_folder, filename))
    ]


def _matching_drive_files(task, drive_files):
    return [
        file for file in drive_files
        if any(document.lower() in file.name.lower() for document in task.required_documents)
    ]


def _folder_name(task, email):
    source = email.sender.split("<")[0].strip() if email and email.sender else "email"
    raw_name = f"{task.title} - {source} - {task.email_id[:12]}"
    clean_name = re.sub(r"[^A-Za-z0-9._ -]+", " ", raw_name)
    clean_name = re.sub(r"\s+", " ", clean_name).strip()
    return clean_name[:100] or f"Task - {task.email_id[:12]}"


def _information_text(task, email, drive_files, copied_files, folder_url):
    lines = [
        "Task information",
        f"Title: {task.title}",
        f"Source email ID: {task.email_id}",
        f"Sender: {email.sender if email else ''}",
        "",
        "Copy-ready email information:",
        email.email_body[:5000] if email else "Email was not found in the local index.",
        "",
        "Required documents:",
        *[f"- {document}" for document in task.required_documents],
        "",
        "Matching Drive metadata:",
    ]
    for file in drive_files:
        lines.extend([
            f"- {file.name}",
            f"  ID: {file.file_id}",
            f"  Parent path: {file.parent_path or '/'}",
            f"  Link: {file.web_view_link or 'unavailable'}",
        ])
    lines.extend(["", "Files copied into this task folder:"])
    lines.extend(f"- {filename}" for filename in copied_files)
    lines.extend(["", f"Task folder: {folder_url or 'unavailable'}"])
    return "\n".join(lines) + "\n"


def _upload_text(text, filename, folder_id):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as file:
        file.write(text)
        local_path = file.name
    try:
        return create_drive_file(local_path, filename, "text/plain", parent_id=folder_id)
    finally:
        os.unlink(local_path)


def _copy_drive_file(file, folder_id):
    suffix = os.path.splitext(file.name)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
        local_path = temporary_file.name
    try:
        download_drive_file(file.file_id, local_path)
        mime_type = file.mime_type or mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        return create_drive_file(local_path, file.name, mime_type, parent_id=folder_id)
    except Exception as error:
        print(f"Could not copy Drive file {file.name}: {error}")
        return None
    finally:
        if os.path.exists(local_path):
            os.unlink(local_path)


def execute_tasks(state: ExecutorState):
    connection = _open_execution_database()
    results = []
    emails_by_id = {email.email_id: email for email in state.get("emails", [])}
    drive_files = state.get("drive_files", [])
    for task in state.get("tasks", []):
        existing = connection.execute(
            "SELECT folder_id, folder_url FROM executed_tasks WHERE task_id = ?",
            (task.task_id,),
        ).fetchone()
        if existing:
            results.append({"task_id": task.task_id, "folder_id": existing[0], "folder_url": existing[1], "status": "already_executed"})
            continue

        folder = create_drive_folder(_folder_name(task, emails_by_id.get(task.email_id)))
        folder_id = folder["id"]
        folder_url = folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder_id}")
        email = emails_by_id.get(task.email_id)
        copied_files = []
        for local_path in _email_attachments(task.email_id):
            uploaded = create_drive_file(
                local_path, os.path.basename(local_path),
                mimetypes.guess_type(local_path)[0] or "application/octet-stream",
                parent_id=folder_id,
            )
            if uploaded:
                copied_files.append(os.path.basename(local_path))
        for drive_file in _matching_drive_files(task, drive_files):
            uploaded = _copy_drive_file(drive_file, folder_id)
            if uploaded:
                copied_files.append(drive_file.name)
        _upload_text(_information_text(task, email, _matching_drive_files(task, drive_files), copied_files, folder_url), "information.txt", folder_id)
        connection.execute(
            "INSERT INTO executed_tasks (task_id, email_id, folder_id, folder_url) VALUES (?, ?, ?, ?)",
            (task.task_id, task.email_id, folder_id, folder_url),
        )
        results.append({"task_id": task.task_id, "folder_id": folder_id, "folder_url": folder_url, "copied_files": len(copied_files), "status": "executed"})
    connection.commit()
    connection.close()
    return {"tasks": state.get("tasks", []), "emails": state.get("emails", []), "drive_files": drive_files, "execution_results": results}


def build_executor_agent():
    graph = StateGraph(ExecutorState)
    graph.add_node("load_planning_context", load_planning_context)
    graph.add_node("analysize_all_emails", analysize_all_emails)
    graph.add_node("get_drive_filenames", get_drive_filenames)
    graph.add_node("get_vector_context", get_vector_context)
    graph.add_node("plan_tasks", plan_tasks)
    graph.add_node("execute_tasks", execute_tasks)
    graph.add_edge(START, "load_planning_context")
    graph.add_edge("load_planning_context", "analysize_all_emails")
    graph.add_edge("analysize_all_emails", "get_drive_filenames")
    graph.add_edge("get_drive_filenames", "get_vector_context")
    graph.add_edge("get_vector_context", "plan_tasks")
    graph.add_edge("plan_tasks", "execute_tasks")
    graph.add_edge("execute_tasks", END)
    return graph.compile()
