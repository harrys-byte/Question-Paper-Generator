import hashlib

_real_md5 = hashlib.md5


def safe_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _real_md5(*args, **kwargs)


hashlib.md5 = safe_md5

from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
import os


def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


def create_plain_text_structured_pdf(input_pdf, output_path):
    raw_text = extract_text_from_pdf(input_pdf)
    lines = [line for line in raw_text.split("\n") if line.strip()]
    
    
    # Now build the structured PDF (unchanged logic)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )
    styles = getSampleStyleSheet()
    custom_styles = [
        ("MainTitle", 16, 20, 0, 20, "Helvetica-Bold", 0),
        ("SubTitle", 12, 16, 0, 10, "Helvetica", 0),
        ("UnitHeading", 14, 18, 30, 20, "Helvetica-Bold", 0),
        ("PartHeading", 13, 18, 25, 15, "Helvetica-Bold", 0),
        ("QuestionNum", 12, 16, 12, 0, "Helvetica-Bold", 20),
        ("QuestionBody", 12, 18, 0, 15, "Helvetica", 40),
        ("COBloom", 11, 14, 0, 10, "Helvetica-Oblique", 40),
    ]
    for name, fs, lead, before, after, font, indent in custom_styles:
        if name not in styles.byName:
            styles.add(
                ParagraphStyle(
                    name=name,
                    fontSize=fs,
                    leading=lead,
                    spaceBefore=before,
                    spaceAfter=after,
                    fontName=font,
                    leftIndent=indent,
                    alignment=1 if "Title" in name or "Heading" in name else 0,
                )
            )
    story = []
    i = 0
    current_question_lines = []
    current_qnum = None
    while i < len(lines):
        line = lines[i]
        # Header
        if any(
            k in line.upper()
            for k in [
                "TEST",
                "REGULATIONS",
                "DEPARTMENT",
                "SEMESTER",
                "COURSE OUTCOMES",
            ]
        ):
            style = "MainTitle" if "TEST" in line.upper() else "SubTitle"
            story.append(Paragraph(line, styles[style]))
            story.append(Spacer(1, 12))
            i += 1
            continue
        if re.match(r"^\d{4}[A-Z]{3}\d{3}T", line):
            story.append(Paragraph(line, styles["SubTitle"]))
            story.append(Spacer(1, 12))
            i += 1
            continue
        if line.startswith("CO") and ":" in line:
            story.append(Paragraph(line, styles["SubTitle"]))
            story.append(Spacer(1, 6))
            i += 1
            continue
        # Unit
        if re.search(r"UNIT\s*[-–]?\s*[IVX12345]+", line, re.I):
            if current_qnum:
                full_text = " ".join(current_question_lines).strip()
                story.append(Paragraph(full_text, styles["QuestionBody"]))
                current_question_lines = []
                current_qnum = None
            story.append(Spacer(1, 20))
            story.append(Paragraph(line, styles["UnitHeading"]))
            story.append(Spacer(1, 15))
            i += 1
            continue
        # Part
        if line.upper().startswith("PART"):
            if current_qnum:
                full_text = " ".join(current_question_lines).strip()
                story.append(Paragraph(full_text, styles["QuestionBody"]))
                current_question_lines = []
                current_qnum = None
            story.append(Spacer(1, 20))
            story.append(Paragraph(line, styles["PartHeading"]))
            story.append(Spacer(1, 12))
            i += 1
            continue
        # Skip table headers
        if any(
            h in line.upper()
            for h in ["Q.NO", "QNO", "QUESTIONS", "CO'S", "BLOOM", "LEVEL"]
        ):
            i += 1
            continue
        # Question number
        qnum_match = re.match(r"^(\d+)[\.\s]*(.*)", line)
        if qnum_match:
            if current_qnum:
                full_text = " ".join(current_question_lines).strip()
                story.append(Paragraph(full_text, styles["QuestionBody"]))
            current_qnum = qnum_match.group(1) + "."
            story.append(Paragraph(current_qnum, styles["QuestionNum"]))
            remaining = qnum_match.group(2).strip()
            current_question_lines = [remaining] if remaining else []
            i += 1
            continue
        # Collect line for current question
        if current_qnum:
            stripped = line.strip()
            # Check for CO Bloom at end of line
            cobloom_match = re.search(r"(CO\d+)\s*(K\d+)$", stripped)
            if cobloom_match:
                main_part = stripped[: cobloom_match.start()].strip()
                if main_part:
                    current_question_lines.append(main_part)
                full_text = " ".join(current_question_lines).strip()
                story.append(Paragraph(full_text, styles["QuestionBody"]))
                # Uniformly place CO Bloom after question on new line
                cobloom_text = f"{cobloom_match.group(1)} {cobloom_match.group(2)}"
                story.append(Paragraph(cobloom_text, styles["COBloom"]))
                current_question_lines = []
                current_qnum = None
            else:
                current_question_lines.append(stripped)
        i += 1
    # Last question
    if current_qnum and current_question_lines:
        full_text = " ".join(current_question_lines).strip()
        story.append(Paragraph(full_text, styles["QuestionBody"]))
    
    doc.build(story)
    print(f"Clean structured PDF created: {output_path}")
    
    return output_path


def course_outcomes(input_pdf):
    raw_text = extract_text_from_pdf(input_pdf)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    
    course_outcomes = []
    co_mode = False
    current_co = ""

    for line in lines:
        line_stripped = line.strip()
        
        if re.match(r"^CO[1-5]:", line_stripped):
            if co_mode and current_co:
                course_outcomes.append(current_co.strip())
            co_mode = True
            current_co = line_stripped
        elif co_mode:
            if re.match(r"^CO[1-5]:", line_stripped):
                course_outcomes.append(current_co.strip())
                current_co = line_stripped
            elif line_stripped and not line_stripped.upper().startswith("UNIT") and "PART" not in line_stripped.upper():
                current_co += " " + line_stripped
            else:
                if current_co:
                    course_outcomes.append(current_co.strip())
                co_mode = False
                if line_stripped.upper().startswith("UNIT") or "PART" in line_stripped.upper():
                    break  # Stop at Unit or PART
    
    # Save last CO if needed
    if co_mode and current_co:
        course_outcomes.append(current_co.strip())
    
    return course_outcomes