import json
import os
import re
import sqlite3
import tempfile
from typing import Optional, TypedDict

import chromadb
from langgraph.graph import END, START, StateGraph
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from google_services.drive import create_drive_file, create_drive_folder, read_drive, download_drive_file
from google_services.gmail import download_attachment, read_gmail
from .extraction_tools import extract_pdf_text, extract_word_documents_text

DOCUMENT_PATTERNS = [
    ("passport", ["passport", "passport copy", "passport photocopy"]),
    ("driver license", ["driver license", "driving licence", "driver's license", "driving license"]),
    ("bank statement", ["bank statement", "bank account statement", "proof of funds"]),
    ("visa", ["visa", "visa document", "visa application"]),
    ("birth certificate", ["birth certificate", "certificate of birth"]),
    ("identity card", ["id card", "identity card", "national id", "government id"]),
    ("proof of address", ["proof of address", "utility bill", "residence proof"]),
    ("transcript", ["transcript", "academic transcript"]),
    ("resume", ["resume", "cv"]),
    ("insurance", ["insurance", "certificate of insurance"]),
]


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
    requires_documents: bool = False
    required_documents: list[str] = Field(default_factory=list)
    deadline_hint: str = ""
    drive_folder_name: str = ""
    drive_folder_id: str = ""
    drive_folder_url: str = ""


class State(TypedDict, total=False):
    emails: list[EmailModel]
    email_snippet_summary: str
    target: Optional[str]


def _data(item):
    return item.model_dump() if hasattr(item, "model_dump") else item


def _extract_deadline_hint(text: str) -> str:
    patterns = [
        r"(?:by|before|due|deadline|latest|no later than)\s*(?:on\s+)?([A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?|\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})|\d{4}-\d{1,2}-\d{1,2})",
        r"(\d{1,2}/\d{1,2}/\d{2,4})",
    ]
    lowered = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def detect_document_needs_for_email(email: dict) -> dict:
    text = f"{email.get('email_title', '')}\n{email.get('email_body', '')}".lower()
    required_documents: list[str] = []
    for canonical_name, aliases in DOCUMENT_PATTERNS:
        if any(alias in text for alias in aliases):
            required_documents.append(canonical_name)
    normalized = list(dict.fromkeys(required_documents))
    deadline_hint = _extract_deadline_hint(f"{email.get('email_title', '')}\n{email.get('email_body', '')}")
    return {
        "requires_documents": bool(normalized),
        "required_documents": normalized,
        "deadline_hint": deadline_hint,
    }


def build_email_folder_name(email_title: str) -> str:
    base = (email_title or "URGENT_EMAIL").strip()
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", " ", base)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    slug = cleaned.upper().replace(" ", "_")
    if not slug:
        slug = "URGENT_EMAIL"
    if len(slug) > 80:
        slug = slug[:80].rstrip("_")
    return f"URGENT_{slug}"


def _write_email_summary_file(folder_id: str, email_title: str, required_documents: list[str], deadline_hint: str):
    document_lines = [f"- {document}" for document in required_documents] if required_documents else ["- None identified"]
    summary = "\n".join([
        f"Subject: {email_title}",
        "Required documents:",
        *document_lines,
        "",
        f"Deadline: {deadline_hint or 'Not specified'}",
    ])
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        handle.write(summary)
        temp_path = handle.name
    try:
        return create_drive_file(temp_path, "document_requirements.txt", "text/plain", parent_id=folder_id)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _upload_email_attachments_to_drive(email_id: str, folder_id: str):
    attachment_folder = os.path.join("downloaded_emails", str(email_id), "attachments")
    if not os.path.isdir(attachment_folder):
        print(f"   ⚠ No attachment folder found for email {email_id}")
        return []
    
    files_in_folder = os.listdir(attachment_folder)
    if not files_in_folder:
        print(f"   ⚠ Attachment folder is empty for email {email_id}")
        return []
    
    uploaded = []
    print(f"   📤 Uploading {len(files_in_folder)} attachment(s) to Drive folder...")
    
    for filename in sorted(files_in_folder):
        path = os.path.join(attachment_folder, filename)
        if not os.path.isfile(path):
            continue
        
        try:
            mime_type = "application/octet-stream"
            if filename.lower().endswith(".pdf"):
                mime_type = "application/pdf"
            elif filename.lower().endswith(".docx"):
                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            print(f"      → Uploading: {filename}")
            uploaded_file = create_drive_file(path, filename, mime_type, parent_id=folder_id)
            if uploaded_file:
                uploaded.append(filename)
                print(f"      ✓ {filename} uploaded successfully")
            else:
                print(f"      ✗ Failed to upload {filename}")
        except Exception as e:
            print(f"      ✗ Error uploading {filename}: {e}")
    
    print(f"   ✓ Uploaded {len(uploaded)}/{len(files_in_folder)} files")
    return uploaded


def classify_document_needs(state: State):
    for item in state.get("emails", []):
        detection = detect_document_needs_for_email({
            "email_title": item.email_title,
            "email_body": item.email_body,
        })
        item.requires_documents = detection["requires_documents"]
        item.required_documents = detection["required_documents"]
        item.deadline_hint = detection["deadline_hint"]
        if item.requires_documents:
            item.drive_folder_name = build_email_folder_name(item.email_title)
        else:
            item.drive_folder_name = ""
        item.drive_folder_id = ""
        item.drive_folder_url = ""
    return state


def sync_document_folders_to_drive(state: State):
    for item in state.get("emails", []):
        if not item.requires_documents:
            continue
        
        print(f"\n📁 Creating Drive folder for: {item.email_title}")
        try:
            folder = create_drive_folder(item.drive_folder_name)
            item.drive_folder_id = str(folder.get("id", ""))
            item.drive_folder_url = folder.get("webViewLink", "")
            
            if not item.drive_folder_id:
                print(f"   ✗ Failed to create folder")
                continue
            
            print(f"   ✓ Folder created: {item.drive_folder_name}")
            print(f"   🔗 URL: {item.drive_folder_url}")
            
            # Write summary file
            print(f"   📝 Writing requirements summary...")
            _write_email_summary_file(item.drive_folder_id, item.email_title, item.required_documents, item.deadline_hint)
            print(f"   ✓ Summary file created")
            
            # Upload attachments
            print(f"   📎 Processing attachments...")
            uploaded_count = len(_upload_email_attachments_to_drive(item.email_id, item.drive_folder_id))
            print(f"   ✓ Total attachments uploaded: {uploaded_count}")
            
        except Exception as e:
            print(f"   ✗ Error creating folder: {e}")
            item.drive_folder_id = ""
            item.drive_folder_url = ""
            continue
    
    return state


def scan_and_add_drive_documents(state: State):
    """Scan Drive for documents and add them to email folders based on content matching."""
    print("\n🔍 Scanning Drive for documents to match emails...")
    
    try:
        # Get all Drive files
        all_drive_files = read_drive()
        document_files = [f for f in all_drive_files if f.get('mimeType', '').startswith('application/') or 
                         any(f.get('name', '').lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.txt'])]
        
        if not document_files:
            print("   ⚠ No documents found on Drive")
            return state
        
        print(f"   ✓ Found {len(document_files)} potential document files on Drive")
        
        # For each email that needs documents, find matching files
        for email_item in state.get("emails", []):
            if not email_item.requires_documents or not email_item.drive_folder_id:
                continue
            
            matched_files = []
            email_text = f"{email_item.email_title} {email_item.email_body}".lower()
            
            print(f"\n   📂 Checking files for: {email_item.email_title}")
            
            for doc_file in document_files:
                file_name = doc_file.get('name', '').lower()
                
                # Check if file name matches any of the required documents
                for required_doc in email_item.required_documents:
                    if required_doc.lower() in file_name or file_name in email_text:
                        matched_files.append(doc_file)
                        print(f"      ✓ Matched: {doc_file.get('name')} (for {required_doc})")
                        break
            
            # Copy matched files to email folder
            if matched_files:
                print(f"   📋 Adding {len(matched_files)} matched document(s)...")
                for doc_file in matched_files:
                    try:
                        # Get the file ID and parents
                        file_id = doc_file.get('id')
                        current_parents = doc_file.get('parents', [])
                        
                        # Add email folder as parent
                        updated_parents = list(set(current_parents + [email_item.drive_folder_id]))
                        
                        # Update the file's parents using Drive API
                        from google_services.setup import validate_user_and_build_service
                        service = validate_user_and_build_service('drive', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'google_services', 'drive_token.json'), 
                                                                 ['https://www.googleapis.com/auth/drive'], 'v3')
                        
                        # Move file to email folder
                        previous_parents = ",".join(current_parents) if current_parents else None
                        new_file = service.files().update(
                            fileId=file_id,
                            addParents=email_item.drive_folder_id,
                            fields='id, parents, webViewLink'
                        ).execute()
                        print(f"      ✓ Added {doc_file.get('name')} to folder")
                    except Exception as e:
                        print(f"      ✗ Error adding {doc_file.get('name')}: {e}")
        
        print("   ✓ Drive document scan complete")
    except Exception as e:
        print(f"   ⚠ Error scanning Drive: {e}")
    
    return state


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
    graph.add_node("classify_document_needs", classify_document_needs)
    graph.add_node("sync_document_folders_to_drive", sync_document_folders_to_drive)
    graph.add_node("scan_and_add_drive_documents", scan_and_add_drive_documents)
    graph.add_node("save_on_sql", save_on_sql)
    graph.add_node("save_on_vector_database", save_on_vector_database)
    graph.add_edge(START, "scan_emails")
    graph.add_edge("scan_emails", "save_emails_locally")
    graph.add_edge("save_emails_locally", "extract_paperwork")
    graph.add_edge("extract_paperwork", "classify_document_needs")
    graph.add_edge("classify_document_needs", "sync_document_folders_to_drive")
    graph.add_edge("sync_document_folders_to_drive", "scan_and_add_drive_documents")
    graph.add_edge("scan_and_add_drive_documents", "save_on_sql")
    graph.add_edge("save_on_sql", "save_on_vector_database")
    graph.add_edge("save_on_vector_database", END)
    return graph.compile()
