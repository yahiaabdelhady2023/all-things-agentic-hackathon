import docx2txt
from pypdf import PdfReader

def extract_pdf_text(filepath):
    reader = PdfReader(filepath)
    raw_text = "\n".join([page.extract_text() for page in reader.pages])
    return raw_text

def extract_word_documents_text(filepath):
    raw_text  = docx2txt.process(filepath)
    return raw_text