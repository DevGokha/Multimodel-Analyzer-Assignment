from fpdf import FPDF
from datetime import datetime
import os
import re


def create_report(analysis_data: dict) -> bytes:
    """
    Step 1: Generates a branded PDF report with full Unicode support.
    Uses DejaVu fonts so any character (emoji, accented, CJK, etc.) renders correctly.
    Returns the PDF as raw bytes ready for download.
    """

    pdf = FPDF()

    # Step 2: Register Unicode-capable DejaVu fonts from the fonts/ directory
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    pdf.add_font('DejaVu', '', os.path.join(font_dir, 'DejaVuSans.ttf'), uni=True)
    pdf.add_font('DejaVu', 'B', os.path.join(font_dir, 'DejaVuSans-Bold.ttf'), uni=True)

    pdf.add_page()

    # Step 3: Draw a branded header bar (full-width blue banner across the top)
    pdf.set_fill_color(0, 123, 255)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_font('DejaVu', 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(8)
    pdf.cell(0, 12, 'Multimodal Analysis Report', 0, 1, 'C')

    # Step 4: Add the generation timestamp below the header
    pdf.set_y(40)
    timestamp = datetime.now().strftime("%d %B %Y, %I:%M %p")
    pdf.set_font('DejaVu', '', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f'Report generated on: {timestamp}', 0, 1, 'R')
    pdf.ln(5)

    # Step 5: Text Analysis section — blue accent bar
    _draw_section_header(pdf, 'Text Analysis', (41, 128, 185))
    # Parse and Draw Sentiment Banner
    sentiment_str = analysis_data.get('text_sentiment', 'N/A')
    match = re.search(r'\(([0-9.]+)\)', sentiment_str)
    score = float(match.group(1)) if match else None
    label_match = re.match(r'^(\w+)', sentiment_str)
    label = label_match.group(1) if label_match else sentiment_str

    if label == 'POSITIVE':
        bg_r, bg_g, bg_b = 209, 250, 229  # Light emerald green
        fg_r, fg_g, fg_b = 6, 95, 70      # Dark emerald green
        icon = "[✓]"
    elif label == 'NEGATIVE':
        bg_r, bg_g, bg_b = 254, 226, 226  # Light rose red
        fg_r, fg_g, fg_b = 153, 27, 27    # Dark rose red
        icon = "[⚠]"
    else:
        bg_r, bg_g, bg_b = 239, 246, 255  # Light gray-blue
        fg_r, fg_g, fg_b = 30, 64, 175    # Dark gray-blue
        icon = "[i]"

    # Draw Sentiment Banner
    current_y = pdf.get_y()
    pdf.set_fill_color(bg_r, bg_g, bg_b)
    pdf.set_draw_color(fg_r, fg_g, fg_b)
    pdf.set_line_width(0.5)
    pdf.rect(10, current_y, 190, 15, 'DF')

    pdf.set_y(current_y + 3)
    pdf.set_x(15)
    pdf.set_font('DejaVu', 'B', 11)
    pdf.set_text_color(fg_r, fg_g, fg_b)
    confidence_pct = f" ({score * 100:.0f}% confidence)" if score is not None else ""
    pdf.cell(0, 9, f"{icon}  SENTIMENT: {label}{confidence_pct}", 0, 1, 'L')
    pdf.ln(5)

    # Draw Topic and candidate list (if available)
    topic_scores = analysis_data.get('topic_scores', [])
    if topic_scores:
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 7, "Topic Classification:", 0, 1)
        pdf.ln(1)
        
        for t in topic_scores:
            t_label = t.get('label', 'N/A')
            t_score = t.get('score', 0.0)
            
            # Print label and percentage
            pdf.set_font('DejaVu', '', 9)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(50, 6, t_label, 0, 0)
            pdf.cell(20, 6, f"{t_score * 100:.0f}%", 0, 0, 'R')
            
            # Draw horizontal bar chart
            bar_x = 85
            bar_y = pdf.get_y() + 1.5
            bar_width = 110
            bar_height = 3
            
            # Background bar
            pdf.set_fill_color(229, 231, 235)
            pdf.rect(bar_x, bar_y, bar_width, bar_height, 'F')
            
            # Active bar
            pdf.set_fill_color(59, 130, 246)
            pdf.rect(bar_x, bar_y, bar_width * t_score, bar_height, 'F')
            pdf.ln(6)
        pdf.ln(3)
    else:
        _add_entry(pdf, "Topic:", analysis_data.get('topic_classification', 'N/A'))

    _add_entry(pdf, "Summary:", analysis_data.get('text_summary', 'N/A'))

    # Step 6: Image Analysis section — green accent bar
    _draw_section_header(pdf, 'Image Analysis', (39, 174, 96))
    # Step 6a: If multiple images were analyzed, render each one separately
    image_results = analysis_data.get('image_results', [])
    if image_results:
        for i, img_result in enumerate(image_results, 1):
            _add_entry(pdf, f"Image {i} ({img_result.get('filename', 'unknown')}):", "")
            _add_entry(pdf, "  Classification:", img_result.get('image_classification', 'N/A'))
            ocr = img_result.get('ocr_text') or "No text found."
            _add_entry(pdf, "  Extracted Text (OCR):", ocr)
    else:
        # Step 6b: Fallback for single-image backward compatibility
        _add_entry(pdf, "Classification:", analysis_data.get('image_classification', 'N/A'))
        ocr_text = analysis_data.get('ocr_text') or "No text found."
        _add_entry(pdf, "Extracted Text (OCR):", ocr_text)

    # Step 7: Final Assessment section — red accent bar
    _draw_section_header(pdf, 'Final Assessment', (231, 76, 60))
    _add_entry(pdf, "Toxicity Warning:", analysis_data.get('toxicity_warning', 'N/A'))
    _add_entry(pdf, "System Response:", analysis_data.get('automated_response', 'N/A'))

    # Step 8: Footer at the bottom of the page
    pdf.set_y(-20)
    pdf.set_font('DejaVu', '', 8)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 10, 'Generated by Multimodal Analyzer', 0, 0, 'C')

    return bytes(pdf.output())


def _draw_section_header(pdf, title, color):
    """
    Step helper: Draw a small colored accent bar on the left and the section title.
    Each section gets its own color for visual distinction in the report.
    """
    r, g, b = color
    pdf.set_fill_color(r, g, b)
    pdf.rect(10, pdf.get_y(), 4, 10, 'F')
    pdf.set_x(18)
    pdf.set_font('DejaVu', 'B', 13)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 10, title, 0, 1)
    pdf.ln(2)


def _add_entry(pdf, label, value):
    """
    Step helper: Add a labeled entry (bold label on one line, value below it).
    Uses DejaVu font for full Unicode character support.
    """
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, label, 0, 1)

    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 6, str(value))
    pdf.ln(4)