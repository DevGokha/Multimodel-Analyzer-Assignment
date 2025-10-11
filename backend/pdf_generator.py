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
    # The 'ln=1' moves the cursor to the next line after printing the label
    pdf.cell(0, 8, label, ln=1)
    
    pdf.set_font('Arial', '', 12)
    # The value is now on its own line and can use the full page width
    pdf.multi_cell(0, 6, value)
    pdf.ln(4) # Add a little space before the next entry

def create_report(analysis_data: dict) -> bytes:
    """Generates a PDF report from the analysis data and returns it as bytes."""

    pdf = FPDF()
    pdf.add_page()
    
    # --- Header ---
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Multimodal Analysis Report', 0, 1, 'C')
    
    # --- Generation Timestamp ---
    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Report generated on: {timestamp}', 0, 1, 'R')
    pdf.ln(10)

    # --- Text Analysis Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Text Analysis', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) # Underline
    pdf.ln(4)
    
    add_section_entry(pdf, "Sentiment:", sanitize_text(analysis_data.get('text_sentiment', 'N/A')))
    add_section_entry(pdf, "Topic:", sanitize_text(analysis_data.get('topic_classification', 'N/A')))
    add_section_entry(pdf, "Summary:", sanitize_text(analysis_data.get('text_summary', 'N/A')))
    
    # --- Image Analysis Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Image Analysis', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) # Underline
    pdf.ln(4)
    
    add_section_entry(pdf, "Classification:", sanitize_text(analysis_data.get('image_classification', 'N/A')))
    ocr_text = analysis_data.get('ocr_text') or "No text found."
    add_section_entry(pdf, "Extracted Text (OCR):", sanitize_text(ocr_text))

    # --- Final Assessment Section ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Final Assessment', ln=1)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) # Underline
    pdf.ln(4)
    
    add_section_entry(pdf, "Toxicity Warning:", sanitize_text(analysis_data.get('toxicity_warning', 'N/A')))
    add_section_entry(pdf, "System Response:", sanitize_text(analysis_data.get('automated_response', 'N/A')))

    # Generate the raw PDF bytes
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes