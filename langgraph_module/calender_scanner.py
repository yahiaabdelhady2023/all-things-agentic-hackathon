import hashlib
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional, TypedDict

from google_services.calender import create_task_calender
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class State(TypedDict):
    events: list
    important_email_ids: list[str]


class CalendarEventModel(BaseModel):
    event_id: str
    email_id: str
    summary: str
    start_time: str
    end_time: str
    description: str
    calendar_link: Optional[str] = None


ACTION_WORDS = (
    "action required", "please reply", "please respond", "reply by",
    "respond by", "response required", "need your reply", "reply needed",
    "deadline", "due by", "appointment", "meeting", "schedule", "confirm",
    "confirmation required",
)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"


def _database_path():
    return os.path.join("databases", "email_database.db")


def _load_emails():
    if not os.path.exists(_database_path()):
        return []
    connection = sqlite3.connect(_database_path())
    rows = connection.execute("SELECT message_id, email_title, sender, email_date, email_body FROM emails").fetchall()
    connection.close()
    return rows


def _event_date(email_date, body):
    current_year = datetime.now(timezone.utc).year
    patterns = [r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", rf"\b({MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,\s*(20\d{{2}}))?\b"]
    for pattern in patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if not match:
            continue
        try:
            if pattern.startswith(r"\b(20"):
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=timezone.utc)
            if "/" in pattern:
                return datetime(int(match.group(3)), int(match.group(1)), int(match.group(2)), tzinfo=timezone.utc)
            month = datetime.strptime(match.group(1), "%B").month
            return datetime(int(match.group(3) or current_year), month, int(match.group(2)), tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        parsed = parsedate_to_datetime(email_date)
        reminder = parsed.astimezone(timezone.utc) + timedelta(days=1)
    except (TypeError, ValueError, OverflowError):
        reminder = datetime.now(timezone.utc) + timedelta(days=1)
    while reminder.weekday() >= 5:
        reminder += timedelta(days=1)
    return reminder.replace(hour=9, minute=0, second=0, microsecond=0)


def scan_important_emails(state: State):
    events = []
    important_ids = []
    for message_id, subject, sender, email_date, body in _load_emails():
        body = body or ""
        if not any(word in f"{subject or ''}\n{body}".lower() for word in ACTION_WORDS):
            continue
        start = _event_date(email_date, body)
        event_id = "reply" + hashlib.sha256(message_id.encode()).hexdigest()[:24]
        events.append(CalendarEventModel(
            event_id=event_id,
            email_id=message_id,
            summary=f"Reply to: {(subject or 'Important email').strip()[:90]}",
            start_time=start.isoformat().replace("+00:00", "Z"),
            end_time=(start + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
            description=f"Reply or follow up on email from {sender or 'unknown sender'}.\nSource Gmail message ID: {message_id}\n\n{body[:4000]}",
        ))
        important_ids.append(message_id)
    return {"events": events, "important_email_ids": important_ids}


def create_calendar_events(state: State):
    os.makedirs("databases", exist_ok=True)
    connection = sqlite3.connect(_database_path())
    connection.execute("CREATE TABLE IF NOT EXISTS calendar_events (event_id TEXT PRIMARY KEY, email_id TEXT NOT NULL UNIQUE, summary TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL, calendar_link TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    events = []
    for event in state.get("events", []):
        existing = connection.execute("SELECT calendar_link FROM calendar_events WHERE event_id = ?", (event.event_id,)).fetchone()
        if existing:
            events.append(event.model_copy(update={"calendar_link": existing[0]}))
            continue
        created = create_task_calender(event.summary, event.start_time, event.end_time, event.description, event.event_id)
        calendar_link = created.get("htmlLink") if created else None
        connection.execute("INSERT INTO calendar_events (event_id, email_id, summary, start_time, end_time, calendar_link) VALUES (?, ?, ?, ?, ?, ?)", (event.event_id, event.email_id, event.summary, event.start_time, event.end_time, calendar_link))
        events.append(event.model_copy(update={"calendar_link": calendar_link}))
    connection.commit()
    connection.close()
    return {"events": events, "important_email_ids": state.get("important_email_ids", [])}


def build_calender_agent():
    graph = StateGraph(State)
    graph.add_node("scan_important_emails", scan_important_emails)
    graph.add_node("create_calendar_events", create_calendar_events)
    graph.add_edge(START, "scan_important_emails")
    graph.add_edge("scan_important_emails", "create_calendar_events")
    graph.add_edge("create_calendar_events", END)
    return graph.compile()


build_calendar_agent = build_calender_agent
