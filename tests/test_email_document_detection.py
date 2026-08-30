import re

from langgraph_module.email_scanner_agent import detect_document_needs_for_email


def test_detect_document_needs_for_email():
    email = {
        "email_title": "Urgent: visa application documents required",
        "email_body": "Please send your passport, bank statement, and driver license before 2026-09-01.",
    }

    result = detect_document_needs_for_email(email)

    assert result["requires_documents"] is True
    assert "passport" in result["required_documents"]
    assert "bank statement" in result["required_documents"]
    assert "driver license" in result["required_documents"]


def test_build_drive_folder_name():
    raw_name = "Urgent: visa application documents required"
    clean = re.sub(r"[^A-Za-z0-9._ -]+", " ", raw_name)
    clean = re.sub(r"\s+", " ", clean).strip()
    expected = "URGENT_" + clean.replace(" ", "_").upper()

    assert expected.startswith("URGENT_")
    assert "VISA" in expected
    assert "DOCUMENTS" in expected
