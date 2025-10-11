from fpdf import FPDF
from datetime import datetime

def sanitize_text(text: str) -> str:
    """
    Removes characters that are not supported by the built-in PDF fonts (latin-1).
    """
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def add_section_entry(pdf, label, value):
    """
    A helper function to add a labeled entry to the PDF with a robust layout.
    """
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, label, ln=1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 6, value)
    pdf.ln(4) 

def create_report(analysis_data: dict) -> bytes:
    """Generates a PDF report from the analysis data and returns it as bytes."""

    pdf = FPDF()
    pdf.add_page()
    
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Multimodal Analysis Report', 0, 1, 'C')
    
    
    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Report generated on: {timestamp}', 0, 1, 'R')
    pdf.ln(10)

    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Text Analysis', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) 
    pdf.ln(4)
    
    add_section_entry(pdf, "Sentiment:", sanitize_text(analysis_data.get('text_sentiment', 'N/A')))
    add_section_entry(pdf, "Topic:", sanitize_text(analysis_data.get('topic_classification', 'N/A')))
    add_section_entry(pdf, "Summary:", sanitize_text(analysis_data.get('text_summary', 'N/A')))
    
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Image Analysis', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) 
    pdf.ln(4)
    
    add_section_entry(pdf, "Classification:", sanitize_text(analysis_data.get('image_classification', 'N/A')))
    ocr_text = analysis_data.get('ocr_text') or "No text found."
    add_section_entry(pdf, "Extracted Text (OCR):", sanitize_text(ocr_text))

    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Final Assessment', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) 
    pdf.ln(4)
    
    add_section_entry(pdf, "Toxicity Warning:", sanitize_text(analysis_data.get('toxicity_warning', 'N/A')))
    add_section_entry(pdf, "System Response:", sanitize_text(analysis_data.get('automated_response', 'N/A')))

    
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes