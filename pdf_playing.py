import docx2txt
from pypdf import PdfReader

def extract_pdf_text():
    reader = PdfReader("peppino_ielts.pdf")
    raw_text = "\n".join([page.extract_text() for page in reader.pages])
    
    print(raw_text)

extract_pdf_text()

def extract_word_documents_text():
    text  = docx2txt.process("fake.docx")
    return text



