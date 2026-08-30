import json
import os
import sqlite3
from typing import Annotated, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from google_services.drive import read_drive

load_dotenv()


class FileModel(BaseModel):
    file_id: str
    name: str
    mime_type: str
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    size: Optional[int] = None
    md5_checksum: Optional[str] = None
    web_view_link: Optional[str] = None
    owner_names: list[str] = Field(default_factory=list)
    owner_emails: list[str] = Field(default_factory=list)
    parent_ids: list[str] = Field(default_factory=list)
    parent_name: str = ""
    parent_path: str = ""
    trashed: bool = False


class State(TypedDict):
    files: Annotated[list[FileModel], list.__add__]


def scan_drive_files(state: State):
    files = [
        FileModel(
            file_id=str(item["id"]),
            name=item.get("name", ""),
            mime_type=item.get("mimeType", ""),
            created_time=item.get("createdTime"),
            modified_time=item.get("modifiedTime"),
            size=int(item["size"]) if item.get("size") else None,
            md5_checksum=item.get("md5Checksum"),
            web_view_link=item.get("webViewLink"),
            owner_names=item.get("owner_names", []),
            owner_emails=item.get("owner_emails", []),
            parent_ids=item.get("parent_ids", item.get("parents", [])),
            parent_name=item.get("parent_name", ""),
            parent_path=item.get("parent_path", ""),
            trashed=item.get("trashed", False),
        )
        for item in read_drive()
    ]
    return {"files": files}


def _open_database():
    os.makedirs("databases", exist_ok=True)
    connection = sqlite3.connect("databases/email_database.db")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS drive_files (
            file_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            created_time TEXT,
            modified_time TEXT,
            size INTEGER,
            md5_checksum TEXT,
            web_view_link TEXT,
            owner_names TEXT NOT NULL DEFAULT '[]',
            owner_emails TEXT NOT NULL DEFAULT '[]',
            parent_ids TEXT NOT NULL DEFAULT '[]',
            parent_name TEXT NOT NULL DEFAULT '',
            parent_path TEXT NOT NULL DEFAULT '',
            trashed INTEGER NOT NULL DEFAULT 0
        )
    """)
    return connection


def save_metadata_drive(state: State):
    connection = _open_database()
    files = state.get("files", [])
    current_file_ids = [
        str((file_item.model_dump() if hasattr(file_item, "model_dump") else file_item)["file_id"])
        for file_item in files
    ]
    if current_file_ids:
        placeholders = ", ".join("?" for _ in current_file_ids)
        connection.execute(
            f"DELETE FROM drive_files WHERE file_id NOT IN ({placeholders})",
            current_file_ids,
        )
    else:
        connection.execute("DELETE FROM drive_files")

    for file_item in files:
        file_data = file_item.model_dump() if hasattr(file_item, "model_dump") else file_item
        connection.execute("""
            INSERT INTO drive_files (
                file_id, name, mime_type, created_time, modified_time, size,
                md5_checksum, web_view_link, owner_names, owner_emails,
                parent_ids, parent_name, parent_path, trashed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                name=excluded.name, mime_type=excluded.mime_type,
                created_time=excluded.created_time, modified_time=excluded.modified_time,
                size=excluded.size, md5_checksum=excluded.md5_checksum,
                web_view_link=excluded.web_view_link, owner_names=excluded.owner_names,
                owner_emails=excluded.owner_emails, parent_ids=excluded.parent_ids,
                parent_name=excluded.parent_name, parent_path=excluded.parent_path,
                trashed=excluded.trashed
        """, (
            str(file_data["file_id"]), file_data["name"], file_data["mime_type"],
            file_data.get("created_time"), file_data.get("modified_time"), file_data.get("size"),
            file_data.get("md5_checksum"), file_data.get("web_view_link"),
            json.dumps(file_data.get("owner_names", [])), json.dumps(file_data.get("owner_emails", [])),
            json.dumps(file_data.get("parent_ids", [])), file_data.get("parent_name", ""),
            file_data.get("parent_path", ""), int(file_data.get("trashed", False)),
        ))
    connection.commit()
    connection.close()
    return state


def build_drive_scanner_agent():
    graph = StateGraph(State)
    graph.add_node("scan_drive_files", scan_drive_files)
    graph.add_node("save_metadata_drive", save_metadata_drive)
    graph.add_edge(START, "scan_drive_files")
    graph.add_edge("scan_drive_files", "save_metadata_drive")
    graph.add_edge("save_metadata_drive", END)
    return graph.compile()