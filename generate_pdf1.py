# generate_pdf.py
import hashlib
import time
_real_md5 = hashlib.md5
def safe_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _real_md5(*args, **kwargs)
hashlib.md5 = safe_md5
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black
from reportlab.platypus import Table, TableStyle
import datetime  # For timestamp in filename

def wrap_text(text, c, max_width, font="Times-Roman", font_size=11):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = current + word + " "
        if c.stringWidth(test, font, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current.strip())
            current = word + " "
    if current:
        lines.append(current.strip())
    return lines

def generate_pdf(header, selected_questions, branch, qcode, output_path, cos, month_year, exam_type="cat1"):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 60
    x_left = margin
    x_right = width - margin
    y = height - 50
    
    # === Reg. No. line - PERFECTLY STRAIGHT ALIGNED as in Image ID: 3 ===
    c.setFont("Times-Roman", 12)  # Normal font
    reg_label = "Reg. No.:"
    label_width = c.stringWidth(reg_label, "Times-Roman", 12)
    
    # Calculate total width and position for perfect right alignment
    box_size = 14
    total_boxes_width = 12 * box_size
    total_reg_width = label_width + 10 + total_boxes_width
    reg_start_x = x_right - total_reg_width

    # Draw label
    c.drawString(reg_start_x, y, reg_label)

    # Draw 12 continuous boxes (perfectly aligned with text baseline)
    box_start_x = reg_start_x + label_width + 10
    box_y = y - 4  # Fine-tuned for perfect straight alignment
    for i in range(12):
        c.rect(box_start_x + i * box_size, box_y, box_size, box_size, fill=0)

    y -= 50  # Move down for Question Paper Code
    
    # Question Paper Code Box
    code = header.get("question_paper_code", qcode)
    c.setStrokeColor(black)
    c.setLineWidth(2)
    c.rect(width / 2 - 100, y - 10, 200, 30, fill=0)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, f"Question Paper Code: {code}")
    y -= 40

    # Degree
    c.setFont("Times-Bold", 16)
    c.drawCentredString(width / 2, y, "B.E. / B.TECH. DEGREE")
    y -= 25

    # Exam Title with Month Year
    title = "CONTINUOUS ASSESSMENT TEST - I" if exam_type == "cat1" else "CONTINUOUS ASSESSMENT TEST - II"
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, f"{title}, {month_year.upper()}")
    y -= 30
    
    # Branch Name
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, branch)
    y -= 20
    
    # Semester & Department
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, header.get("semester", ""))
    y -= 20
    c.drawCentredString(width / 2, y, header.get("department", ""))
    y -= 30

    # Subject
    subject = f"{header.get('subject_code', '')} - {header.get('subject_name', '')}"
    c.setFont("Times-Bold", 13)
    c.drawCentredString(width / 2, y, subject)
    y -= 25

    # Regulations
    c.setFont("Times-Roman", 12)
    c.drawCentredString(width / 2, y, header.get("regulation", ""))
    y -= 40

    # Time and Marks
    c.setFont("Times-Roman", 12)
    c.drawString(x_left, y, "Time: 90 Minutes")
    c.drawRightString(x_right, y, "Maximum Marks: 50 Marks")
    y -= 40

    # Course Outcomes
    c.setFont("Times-Bold", 12)
    c.drawString(x_left, y, "Course Outcomes:")
    y -= 20
    c.setFont("Times-Roman", 11)
    for i in cos:
        c.drawString(x_left, y, i)
        y -= 18
    y -= 15

    # Bloom's Taxonomy Table
    bloom_data = [
        ["K1-Remember", "K2-Understand", "K3-Apply", "K4-Analyse", "K5-Evaluate", "K6-Create"]
    ]
    bloom_table = Table(bloom_data, colWidths=(width - 2*margin)/6)
    bloom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), '#FFFFFF'),  
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 1, black),
    ]))
    w, h = bloom_table.wrap(width - 2*margin, y)
    bloom_table.drawOn(c, margin, y - h)
    y -= 10
    y -= h + 30

    # PART A - Ensure heading and first question on same page
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART A – (5 x 2 = 10 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 30  # Space before questions

    # Check space for heading + first question
    if y < 50:  # Safe threshold
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    q_no = 1
    for q in selected_questions["PART_A"]:
        wrapped = wrap_text(q.text, c, x_right - x_left - 80)
        c.drawString(x_left, y, f"{q_no}. {wrapped[0]}")
        y -= 15
        for line in wrapped[1:]:
            c.drawString(x_left + 20, y, line)
            y -= 20
        c.drawRightString(x_right, y + 15, f"{q.co} {q.bloom}")
        y -= 10
        q_no += 1

    if y < 200:  # Safe threshold
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    
    # PART B - Ensure heading and first question on same page
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART B – (2 x 13 = 26 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 30

    # Check space for heading + first OR pair
    if y < 100:  # Enough for one full OR pair
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    for idx, pair in enumerate(selected_questions["PART_B"], start=6):
        main = pair["main"]
        or_q = pair["or"]

        # Check space for full OR pair
        if y < 250:
            c.showPage()
            y = height - 60
            c.setFont("Times-Roman", 11)

        # Main question
        wrapped = wrap_text(main.text, c, x_right - x_left - 80)
        c.drawString(x_left, y, f"{idx}. {wrapped[0]}")
        y -= 15
        for line in wrapped[1:]:
            c.drawString(x_left + 25, y, line)
            y -= 15
        c.drawRightString(x_right, y + 15, f"{main.co} {main.bloom}")
        y -= 15

        # (OR)
        c.setFont("Times-Italic", 12)
        c.drawCentredString(width / 2, y, "(OR)")
        y -= 20

        # OR question
        c.setFont("Times-Roman", 11)
        wrapped_or = wrap_text(or_q.text, c, x_right - x_left - 100)
        c.drawString(x_left + 10, y, wrapped_or[0])
        y -= 15
        for line in wrapped_or[1:]:
            c.drawString(x_left + 25, y, line)
            y -= 15
        c.drawRightString(x_right, y + 15, f"{or_q.co} {or_q.bloom}")
        y -= 30
    
    if y < 100:  # Safe threshold
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    # PART C - Ensure heading and first question on same page, proper alignment
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART C – (1 x 14 = 14 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 30

    # Check space for heading + first question
    if y < 200:
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    part_c_qs = selected_questions["PART_C"]
    q_no = 10 if exam_type in ["cat1", "cat2"] else 16  # Adjust for endsem if needed

    for i, q in enumerate(part_c_qs):
        if y < 150:
            c.showPage()
            y = height - 60
            c.setFont("Times-Roman", 11)

        wrapped = wrap_text(q.text, c, x_right - x_left - 80)
        if i == 0:
            # First question: full number and alignment like others
            c.drawString(x_left, y, f"{q_no}. (a) {wrapped[0]}")
        else:
            # OR question: indented, no number prefix
            c.drawString(x_left + 15, y, "(b) "+wrapped[0])

        y -= 15
        for line in wrapped[1:]:
            indent = 30 if i == 0 else 30
            c.drawString(x_left + indent, y, line)
            y -= 15

        c.drawRightString(x_right, y + 15, f"{q.co} {q.bloom}")
        y -= 25

        if i == 0 and len(part_c_qs) > 1:
            c.setFont("Times-Italic", 12)
            c.drawCentredString(width / 2, y, "(OR)")
            y -= 20
            c.setFont("Times-Roman", 11)

    # Generate unique filename with timestamp (outside function if needed, but here for completeness)
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Note: output_path is already provided, so no change here
    c.save()
    

def generate_pdf_endsem(header, selected_questions, branch, qcode, output_path, cos, month_year, tallow, exam_type="endsem"):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 60
    x_left = margin
    x_right = width - margin
    y = height - 50
    
    # === Reg. No. line - PERFECTLY STRAIGHT ALIGNED as in Image ID: 3 ===
    c.setFont("Times-Roman", 12)  # Normal font
    reg_label = "Reg. No.:"
    label_width = c.stringWidth(reg_label, "Times-Roman", 12)
    
    # Calculate total width and position for perfect right alignment
    box_size = 14
    total_boxes_width = 12 * box_size
    total_reg_width = label_width + 10 + total_boxes_width
    reg_start_x = x_right - total_reg_width

    # Draw label
    c.drawString(reg_start_x, y, reg_label)

    # Draw 12 continuous boxes (perfectly aligned with text baseline)
    box_start_x = reg_start_x + label_width + 10
    box_y = y - 4  # Fine-tuned for perfect straight alignment
    for i in range(12):
        c.rect(box_start_x + i * box_size, box_y, box_size, box_size, fill=0)

    y -= 50  # Move down for Question Paper Code

    # Question Paper Code Box
    code = header.get("question_paper_code", qcode)
    c.setStrokeColor(black)
    c.setLineWidth(2)
    c.rect(width / 2 - 100, y - 10, 200, 30, fill=0)
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, f"Question Paper Code: {code}")
    y -= 35

    # Exam Title with Month Year
    title = "REGULAR EXAMINATIONS"
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, f"{month_year.upper()} {title}")
    y -= 25
    
    # Degree
    c.setFont("Times-Bold", 16)
    c.drawCentredString(width / 2, y, "B.E. / B.TECH. DEGREE")
    y -= 25

    # Semester & Department
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, header.get("semester", ""))
    y -= 20
    
    # Branch Name
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, branch)
    y -= 20
    

    # Subject
    subject = f"{header.get('subject_code', '')} - {header.get('subject_name', '')}"
    c.setFont("Times-Bold", 13)
    c.drawCentredString(width / 2, y, subject)
    y -= 25
    
    # Common to
    c.setFont("Times-Roman", 12)
    c.drawCentredString(width / 2, y, header.get("department", ""))
    y -= 25
    
    # Permitted items
    c.drawCentredString(width / 2, y, tallow)
    y -= 25

    # Regulations
    c.setFont("Times-Roman", 12)
    c.drawCentredString(width / 2, y, header.get("regulation", ""))
    y -= 40

    # Time and Marks
    c.setFont("Times-Roman", 12)
    c.drawString(x_left, y, "Time: 180 Minutes")
    c.drawRightString(x_right, y, "Maximum: 100 Marks")
    y -= 25

    # Course Outcomes
    c.setFont("Times-Bold", 12)
    c.drawString(x_left, y, "Course Outcomes:")
    y -= 20
    c.setFont("Times-Roman", 11)
    for i in cos:
        c.drawString(x_left, y, i)
        y -= 18
    y -= 5

    # Bloom's Taxonomy Table
    bloom_data = [
        ["K1-Remember", "K2-Understand", "K3-Apply", "K4-Analyse", "K5-Evaluate", "K6-Create"]
    ]
    bloom_table = Table(bloom_data, colWidths=(width - 2*margin)/6)
    bloom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), '#FFFFFF'),  # Changed to black for visibility if needed, but typically light
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 1, black),
    ]))
    w, h = bloom_table.wrap(width - 2*margin, y)
    bloom_table.drawOn(c, margin, y - h)
    y -= 10
    y -= h + 30

    # PART A - Ensure heading and first question on same page
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART A – (10 x 2 = 20 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 25  # Space before questions

    # Check space for heading + first question
    if y < 50:  # Safe threshold
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    q_no = 1
    for q in selected_questions["PART_A"]:
        wrapped = wrap_text(q.text, c, x_right - x_left - 80)
        c.drawString(x_left, y, f"{q_no}. {wrapped[0]}")
        y -= 15
        for line in wrapped[1:]:
            c.drawString(x_left + 20, y, line)
            y -= 15
        c.drawRightString(x_right, y + 15, f"{q.co} {q.bloom}")
        y -= 5
        q_no += 1

    y -= 20
    c.showPage()
    y = height - 60
    
    # PART B - Ensure heading and first question on same page
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART B – (5 x 13 = 65 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 30

    # Check space for heading + first OR pair
    if y < 100:  # Enough for one full OR pair
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    for idx, pair in enumerate(selected_questions["PART_B"], start=6):
        main = pair["main"]
        or_q = pair["or"]

        # Check space for full OR pair
        if y < 250:
            c.showPage()
            y = height - 60
            c.setFont("Times-Roman", 11)

        # Main question
        wrapped = wrap_text(main.text, c, x_right - x_left - 80)
        c.drawString(x_left, y, f"{idx}. {wrapped[0]}")
        y -= 15
        for line in wrapped[1:]:
            c.drawString(x_left + 25, y, line)
            y -= 15
        c.drawRightString(x_right, y + 15, f"{main.co} {main.bloom}")
        y -= 15

        # (OR)
        c.setFont("Times-Italic", 12)
        c.drawCentredString(width / 2, y, "(OR)")
        y -= 20

        # OR question
        c.setFont("Times-Roman", 11)
        wrapped_or = wrap_text(or_q.text, c, x_right - x_left - 100)
        c.drawString(x_left + 10, y, wrapped_or[0])
        y -= 15
        for line in wrapped_or[1:]:
            c.drawString(x_left + 25, y, line)
            y -= 15
        c.drawRightString(x_right, y + 15, f"{or_q.co} {or_q.bloom}")
        y -= 30

    # Check space for heading + first OR pair
    if y < 100:  # Enough for one full OR pair
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)
        
    # PART C - Ensure heading and first question on same page, proper alignment
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, y, "PART C – (1 x 15 = 15 marks)")
    y -= 25
    c.setFont("Times-Bold", 12)
    c.drawCentredString(width / 2, y, "Answer ALL Questions")
    y -= 30

    # Check space for heading + first question
    if y < 200:
        c.showPage()
        y = height - 60
        c.setFont("Times-Roman", 11)

    c.setFont("Times-Roman", 11)
    part_c_qs = selected_questions["PART_C"]
    q_no = 16  # Adjust for endsem if needed

    for i, q in enumerate(part_c_qs):
        if y < 150:
            c.showPage()
            y = height - 60
            c.setFont("Times-Roman", 11)

        wrapped = wrap_text(q.text, c, x_right - x_left - 80)
        if i == 0:
            # First question: full number and alignment like others
            c.drawString(x_left, y, f"{q_no}. (a) {wrapped[0]}")
        else:
            # OR question: indented, no number prefix
            c.drawString(x_left + 15, y, "(b) "+wrapped[0])

        y -= 15
        for line in wrapped[1:]:
            indent = 30 if i == 0 else 30
            c.drawString(x_left + indent, y, line)
            y -= 15

        c.drawRightString(x_right, y + 15, f"{q.co} {q.bloom}")
        y -= 25

        if i == 0 and len(part_c_qs) > 1:
            c.setFont("Times-Italic", 12)
            c.drawCentredString(width / 2, y, "(OR)")
            y -= 20
            c.setFont("Times-Roman", 11)
            
    c.save()