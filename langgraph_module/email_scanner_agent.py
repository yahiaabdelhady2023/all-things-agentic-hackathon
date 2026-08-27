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
from google_services.gmail import read_gmail , download_attachment
from datetime import datetime
from .extraction_tools import extract_pdf_text, extract_word_documents_text
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
import sqlite3

load_dotenv()

################################################################
# 1. Model Configuration                                        #
################################################################

# Fixed model name to a valid Gemini model
llm = init_chat_model(model="gemini-2.5-flash", model_provider="google_genai")

################################################################
# 2. Data Models                                                #
################################################################

class AttachmentModel(BaseModel):
    attachment_id: int
    attachment_filename: str
    attachment_content: str

class EmailModel(BaseModel):
    email_id: int
    email_title: str
    email_snippet: str
    has_attachment: bool
    sender: str
    downloaded_locally: bool
    email_date: datetime
    email_body: str
    attachment_ids: Optional[list[str]]
    attachment_filenames: Optional[list[str]]
    attachment_objects: Optional[list[AttachmentModel]]
################################################################
# 3. State                                                      #
################################################################


class State(TypedDict):
    emails: Annotated[list[EmailModel], operator.add]
    email_snippet_summary: str
    target: Optional[str]

################################################################
# 4. Validation Models                                          #
################################################################


class CreateEmailModel_Schema(BaseModel):
    emails: list[EmailModel] = Field(description="""
    create email model based on data given, and save them in list

    NOTE:
    1. for downloaded_locally flag SET it to 'false' boolean, initally!
    """)
    email_snippet_summary: str = Field(description="""
        based on emails given to you, make a summary
    """)



################################################################
# 5. Nodes                                                     #
################################################################

def scan_emails(state: State):

    #what do you do?
    #i call Google Services API 
    # i iterate through emails
    # i convert them to EmailModel and save them in list
    # I create summary of i witnessed!
    
    emails = read_gmail()
    emails = str(emails)
    # how do i pass bunch of emails to basemodel instead of it, and get them in email format?
    llm_create_email_schema = llm.with_structured_output(CreateEmailModel_Schema)
    result = llm_create_email_schema.invoke(emails)
    return {"emails":result.emails,"email_snippet_summary":result.email_snippet_summary}


def save_emails_locally(state):
    print("==========================="*10)
    print("emails are", state.get("emails"))
    print("==========================="*10)
    print("summary is", state.get("email_snippet_summary"))
    print("==========================="*10)
    
    emails = state.get("emails", [])
    
    # Base folder where all emails will be saved
    base_save_folder = "downloaded_emails"
    os.makedirs(base_save_folder, exist_ok=True)
    
    for email_item in emails:
        # Handle both Pydantic EmailModel objects and raw dictionaries
        if hasattr(email_item, 'model_dump'):
            email_data = email_item.model_dump()
        elif hasattr(email_item, 'dict'):
            email_data = email_item.dict()
        else:
            email_data = email_item
            
        # Get the ID (handling both 'id' from your dict and 'email_id' from your model)
        msg_id = email_data.get("id") or email_data.get("email_id")
        
        if not msg_id:
            print("Skipping an email because no ID was found.")
            continue
            
        # Create a dedicated folder for this specific email
        email_folder = os.path.join(base_save_folder, str(msg_id))
        os.makedirs(email_folder, exist_ok=True)
        
        # 1. Save the email text and metadata to a JSON file
        metadata_file = os.path.join(email_folder, "email_content.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            # We use default=str to handle datetime objects from EmailModel
            json.dump(email_data, f, indent=4, default=str)
        
        print(f"Saved text/metadata for email {msg_id} to {metadata_file}")
        
        # 2. Download attachments if they exist
        if email_data.get("has_attachment"):
            attachment_ids = email_data.get("attachment_ids", [])
            attachment_filenames = email_data.get("attachment_filenames", [])
            
            # Combine the IDs and filenames using zip
            for att_id, att_name in zip(attachment_ids, attachment_filenames):
                if att_id and att_name:
                    attachments_folder = os.path.join(email_folder, "attachments")
                    print(f"Downloading attachment '{att_name}' for email {msg_id}...")
                    
                    # Call your existing download function
                    download_attachment(
                        message_id=msg_id,
                        attachment_id=att_id,
                        file_name=att_name,
                        save_folder=attachments_folder
                    )
                    
    # Update state if necessary (e.g., mark as downloaded)
    state["emails_downloaded"] = True 
    
    return state


def extract_paperwork(state: State):
    emails = state.get("emails", [])
    updated_emails = []
    
    # This must match the folder structure from your `save_emails_locally` function
    base_save_folder = "downloaded_emails"
    
    # Initialize the structured LLM parser outside the loop
    llm_attachment = llm.with_structured_output(AttachmentModel)

    for email_item in emails:
        # 1. Handle whether the email is a Pydantic object or a standard dictionary
        if hasattr(email_item, 'model_dump'):
            email_data = email_item.model_dump()
            email_id = email_item.email_id
        else:
            email_data = email_item
            email_id = email_data.get("email_id") or email_data.get("id")

        # 2. Safely grab attachment lists
        attachment_ids = email_data.get("attachment_ids") or []
        attachment_filenames = email_data.get("attachment_filenames") or []
        attachment_objects_list = []

        # 3. Iterate through attachments if they exist
        if email_data.get("has_attachment") and attachment_ids and attachment_filenames:
            for att_id, filename in zip(attachment_ids, attachment_filenames):
                
                # Construct the correct path to where the file was saved
                attachments_folder = os.path.join(base_save_folder, str(email_id), "attachments")
                file_path = os.path.join(attachments_folder, filename)
                
                # Skip if the file wasn't actually downloaded
                if not os.path.exists(file_path):
                    print(f"Could not find file: {file_path}")
                    continue

                raw_text = ""
                
                # 4. Extract text based on file extension
                if filename.lower().endswith(".pdf"):
                    raw_text = extract_pdf_text(file_path)
                elif filename.lower().endswith(".docx"):
                    # Fixed: calling the correct word document extractor
                    raw_text = extract_word_documents_text(file_path)
                else:
                    print(f"Unsupported file type for extraction: {filename}")
                    continue

                # 5. Pass extracted text to LLM to map it to AttachmentModel
                if raw_text:
                    try:
                        # You can also format a string here if you want to give the LLM more context
                        # e.g., f"Parse this document named {filename}:\n\n{raw_text}"
                        attachment_object = llm_attachment.invoke(raw_text)
                        
                        # Overwrite the ID and filename just in case the LLM hallucinates them
                        # (since it's only looking at the raw text)
                        attachment_object.attachment_id = att_id
                        attachment_object.attachment_filename = filename
                        
                        attachment_objects_list.append(attachment_object)
                    except Exception as e:
                        print(f"Failed to parse attachment {filename} with LLM: {e}")

        # 6. Update the email object with the new attachment data
        if hasattr(email_item, 'model_dump'):
            email_item.attachment_objects = attachment_objects_list
            updated_emails.append(email_item)
        else:
            email_data["attachment_objects"] = attachment_objects_list
            updated_emails.append(email_data)

    # 7. Return the updated state
    return {"emails": updated_emails}


def save_on_sql(state: State):
    # 1. Ensure the database directory exists
    os.makedirs("./databases", exist_ok=True)
    
    # 2. Connect to SQLite (this will create the file if it doesn't exist)
    conn = sqlite3.connect("./databases/email_database.db")
    cursor = conn.cursor()

    # 3. Create the standard relational tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            email_id TEXT PRIMARY KEY,
            email_title TEXT,
            email_snippet TEXT,
            sender TEXT,
            email_date TEXT,
            email_body TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            attachment_id TEXT PRIMARY KEY,
            email_id TEXT,
            filename TEXT,
            content TEXT,
            FOREIGN KEY(email_id) REFERENCES emails(email_id)
        )
    ''')

    emails = state.get("emails", [])
    
    # 4. Iterate through state and insert records
    for email_item in emails:
        # Standardize data access whether it's a Pydantic object or dict
        if hasattr(email_item, 'model_dump'):
            email = email_item.model_dump()
        else:
            email = email_item if isinstance(email_item, dict) else email_item.dict()

        email_id = str(email.get("email_id"))

        # Insert Email Data
        cursor.execute('''
            INSERT OR REPLACE INTO emails 
            (email_id, email_title, email_snippet, sender, email_date, email_body)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            email_id,
            email.get("email_title", ""),
            email.get("email_snippet", ""),
            email.get("sender", ""),
            str(email.get("email_date", "")), # Convert datetime to string
            email.get("email_body", "")
        ))

        # Insert Attachment Data
        attachment_objects = email.get("attachment_objects") or []
        for att in attachment_objects:
            if hasattr(att, 'model_dump'):
                att_dict = att.model_dump()
            else:
                att_dict = att if isinstance(att, dict) else att.dict()

            cursor.execute('''
                INSERT OR REPLACE INTO attachments
                (attachment_id, email_id, filename, content)
                VALUES (?, ?, ?, ?)
            ''', (
                str(att_dict.get("attachment_id")),
                email_id,
                att_dict.get("attachment_filename", ""),
                att_dict.get("attachment_content", "")
            ))

    # 5. Commit changes and close the connection
    conn.commit()
    conn.close()
    print(f"Successfully saved {len(emails)} emails and their attachments to SQLite!")
    
    return state



def save_on_vector_database(state: State):
    client = chromadb.PersistentClient(path="./databases/vector_db")
    collection = client.get_or_create_collection(name="email_and_attachments")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100 
    )

    documents_to_insert = []
    metadata_to_insert = []
    ids_to_insert = []

    emails = state.get("emails", [])
    
    for email_item in emails:
        # Standardize data access
        if hasattr(email_item, 'model_dump'):
            email = email_item.model_dump()
        else:
            email = email_item if isinstance(email_item, dict) else email_item.dict()

        email_id = str(email.get("email_id"))
        email_body = email.get("email_body", "")
        
        # 1. Process the Email Body
        if email_body:
            email_chunks = text_splitter.split_text(email_body)
            for i, chunk in enumerate(email_chunks):
                documents_to_insert.append(chunk)
                ids_to_insert.append(f"email_{email_id}_chunk_{i}")
                
                metadata_to_insert.append({
                    "type": "email",
                    "email_id": email_id,
                    "sender": email.get("sender", "unknown"),
                    "date": str(email.get("email_date", "unknown")),
                    "chunk_index": i
                })

        # 2. Process the Attachments natively from your state structure
        attachment_objects = email.get("attachment_objects") or []
        for att in attachment_objects:
            if hasattr(att, 'model_dump'):
                att_dict = att.model_dump()
            else:
                att_dict = att if isinstance(att, dict) else att.dict()
                
            att_id = str(att_dict.get("attachment_id"))
            att_content = att_dict.get("attachment_content", "")
            
            if att_content:
                attachment_chunks = text_splitter.split_text(att_content)
                for i, chunk in enumerate(attachment_chunks):
                    documents_to_insert.append(chunk)
                    ids_to_insert.append(f"att_{att_id}_chunk_{i}")
                    
                    metadata_to_insert.append({
                        "type": "attachment",
                        "attachment_id": att_id,
                        "email_id": email_id, # Crucial link back to the email
                        "filename": att_dict.get("attachment_filename", "unknown"),
                        "chunk_index": i
                    })

    # 3. Batch insert into Chroma
    if documents_to_insert:
        collection.add(
            documents=documents_to_insert,
            metadatas=metadata_to_insert,
            ids=ids_to_insert
        )
        print(f"Successfully saved {len(documents_to_insert)} chunks to ChromaDB!")
    
    return state





################################################################
# 6. Graph Build                                               #
################################################################


def build_email_scanner_agent() -> StateGraph:
    graph = StateGraph(State)
    graph.add_node("scan_emails",scan_emails)
    graph.add_node("save_emails_locally",save_emails_locally)
    graph.add_node("save_on_sql",save_on_sql)
    graph.add_node("save_on_vector_database",save_on_vector_database)

    graph.add_edge(START,"scan_emails")
    graph.add_edge("scan_emails","save_emails_locally")
    graph.add_edge("save_emails_locally","save_on_sql")
    graph.add_edge("save_on_sql","save_on_vector_database")
    graph.add_edge("save_on_vector_database",END)

    graph = graph.compile()
    bytes_graph = graph.get_graph().draw_mermaid_png()
    io_bytes_graph = io.BytesIO(bytes_graph)
    img = Image.open(io_bytes_graph)
    img.show("hello")

    return graph

################################################################
# 7. Agent Initialization                                        #
################################################################

# build_email_scanner_agent()

