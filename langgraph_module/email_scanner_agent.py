import json
import os
import sqlite3
from typing import Optional, TypedDict

import chromadb
from langgraph.graph import END, START, StateGraph
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from google_services.gmail import download_attachment, read_gmail
from .extraction_tools import extract_pdf_text, extract_word_documents_text


class AttachmentModel(BaseModel):
    attachment_id: str
    attachment_filename: str
    attachment_content: str


class EmailModel(BaseModel):
    email_id: str
    email_title: str
    email_snippet: str
    has_attachment: bool
    sender: str
    downloaded_locally: bool = False
    email_date: str
    email_body: str
    attachment_ids: list[str] = Field(default_factory=list)
    attachment_filenames: list[str] = Field(default_factory=list)
    attachment_objects: list[AttachmentModel] = Field(default_factory=list)


class State(TypedDict, total=False):
    emails: list[EmailModel]
    email_snippet_summary: str
    target: Optional[str]


def _data(item):
    return item.model_dump() if hasattr(item, "model_dump") else item


def scan_emails(state: State):
    emails = []
    for raw_email in read_gmail(query=(state.get("target") or "").strip() or None):
        attachments = raw_email.get("attachments", [])
        emails.append(EmailModel(
            email_id=str(raw_email["id"]),
            email_title=raw_email.get("email_title", "No Subject"),
            email_snippet=raw_email.get("email_snippet", ""),
            has_attachment=bool(attachments),
            sender=raw_email.get("sender", "Unknown Sender"),
            email_date=str(raw_email.get("email_date", "Unknown Date")),
            email_body=raw_email.get("email_body", ""),
            attachment_ids=[str(item["attachment_id"]) for item in attachments],
            attachment_filenames=[item["filename"] for item in attachments],
        ))
    return {"emails": emails, "email_snippet_summary": f"Found {len(emails)} matching email(s)."}


def save_emails_locally(state: State):
    for item in state.get("emails", []):
        email = _data(item)
        message_id = str(email["email_id"])
        folder = os.path.join("downloaded_emails", message_id)
        attachment_folder = os.path.join(folder, "attachments")
        os.makedirs(attachment_folder, exist_ok=True)
        email["downloaded_locally"] = True
        with open(os.path.join(folder, "email_content.json"), "w", encoding="utf-8") as file:
            json.dump(email, file, indent=2, default=str)
        for attachment_id, filename in zip(email["attachment_ids"], email["attachment_filenames"]):
            safe_filename = os.path.basename(filename)
            path = os.path.join(attachment_folder, safe_filename)
            if not os.path.exists(path):
                download_attachment(message_id, attachment_id, safe_filename, attachment_folder)
        item.downloaded_locally = True
    return state


def extract_paperwork(state: State):
    for item in state.get("emails", []):
        email = _data(item)
        objects = []
        for attachment_id, filename in zip(email["attachment_ids"], email["attachment_filenames"]):
            path = os.path.join("downloaded_emails", email["email_id"], "attachments", os.path.basename(filename))
            if not os.path.exists(path):
                continue
            if filename.lower().endswith(".pdf"):
                content = extract_pdf_text(path)
            elif filename.lower().endswith(".docx"):
                content = extract_word_documents_text(path)
            else:
                content = ""
            if content:
                objects.append(AttachmentModel(attachment_id=attachment_id, attachment_filename=filename, attachment_content=content))
        item.attachment_objects = objects
    return state


def _connection():
    os.makedirs("databases", exist_ok=True)
    connection = sqlite3.connect("databases/email_database.db")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("""CREATE TABLE IF NOT EXISTS emails (message_id TEXT PRIMARY KEY, email_title TEXT, email_snippet TEXT, sender TEXT, email_date TEXT, email_body TEXT)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS attachments (message_id TEXT NOT NULL, attachment_id TEXT NOT NULL, filename TEXT NOT NULL, content TEXT, PRIMARY KEY(message_id, attachment_id), FOREIGN KEY(message_id) REFERENCES emails(message_id) ON DELETE CASCADE)""")
    return connection


def save_on_sql(state: State):
    connection = _connection()
    for item in state.get("emails", []):
        email = _data(item)
        message_id = str(email["email_id"])
        connection.execute("""INSERT INTO emails VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(message_id) DO UPDATE SET email_title=excluded.email_title, email_snippet=excluded.email_snippet, sender=excluded.sender, email_date=excluded.email_date, email_body=excluded.email_body""", (message_id, email["email_title"], email["email_snippet"], email["sender"], email["email_date"], email["email_body"]))
        extracted = {str(_data(att)["attachment_id"]): _data(att) for att in email.get("attachment_objects", [])}
        for attachment_id, filename in zip(email["attachment_ids"], email["attachment_filenames"]):
            connection.execute("""INSERT INTO attachments VALUES (?, ?, ?, ?) ON CONFLICT(message_id, attachment_id) DO UPDATE SET filename=excluded.filename, content=excluded.content""", (message_id, attachment_id, filename, extracted.get(str(attachment_id), {}).get("attachment_content", "")))
    connection.commit()
    connection.close()
    return state


def save_on_vector_database(state: State):
    collection = chromadb.PersistentClient(path="databases/vector_db").get_or_create_collection(name="email_and_attachments")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    documents, metadatas, ids = [], [], []
    for item in state.get("emails", []):
        email = _data(item)
        message_id = str(email["email_id"])
        for index, chunk in enumerate(splitter.split_text(email["email_body"])):
            documents.append(chunk); ids.append(f"email_{message_id}_chunk_{index}"); metadatas.append({"type": "email", "email_id": message_id})
        for attachment in email.get("attachment_objects", []):
            att = _data(attachment)
            for index, chunk in enumerate(splitter.split_text(att["attachment_content"])):
                documents.append(chunk); ids.append(f"attachment_{message_id}_{att['attachment_id']}_chunk_{index}"); metadatas.append({"type": "attachment", "email_id": message_id, "attachment_id": att["attachment_id"], "filename": att["attachment_filename"]})
    if documents:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    return state


def build_email_scanner_agent():
    graph = StateGraph(State)
    graph.add_node("scan_emails", scan_emails)
    graph.add_node("save_emails_locally", save_emails_locally)
    graph.add_node("extract_paperwork", extract_paperwork)
    graph.add_node("save_on_sql", save_on_sql)
    graph.add_node("save_on_vector_database", save_on_vector_database)
    graph.add_edge(START, "scan_emails")
    graph.add_edge("scan_emails", "save_emails_locally")
    graph.add_edge("save_emails_locally", "extract_paperwork")
    graph.add_edge("extract_paperwork", "save_on_sql")
    graph.add_edge("save_on_sql", "save_on_vector_database")
    graph.add_edge("save_on_vector_database", END)
    return graph.compile()
