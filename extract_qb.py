import pdfplumber
import re
from question import Question


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
            if page_text:
                text += page_text + "\n"
    return text


def extract_header(text):
    header = {
        "exam_type": None,
        "subject_code": None,
        "subject_name": None,
        "regulation": None,
        "department": None,
        "semester": None,
    }
    lines = text.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if "CONTINUOUS ASSESSMENT TEST" in line.upper():
            header["exam_type"] = line
        if "Regulations R" in line:
            header["regulation"] = line
        if "Department" in line:
            header["department"] = line
        if "Year" in line and "Semester" in line:
            header["semester"] = line
            
        # Subject Code + Name
        subj_match = re.search(r"(\d{4}[A-Z]{3}\d{3}T|[A-Z]{3}\d{3}T)\s*[-–]?\s*(.+)", line)
        if subj_match:
            header["subject_code"] = subj_match.group(1)
            subject_name = subj_match.group(2).strip()
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                if re.match(r"^CO[1-5]:", next_line) or "Unit" in next_line or "PART" in next_line.upper():
                    break
                subject_name += " " + next_line
                j += 1
            header["subject_name"] = subject_name.strip()
            continue
            
    return header


def extract_questions(text):
    questions = []
    current_unit = None
    current_part = None
    collecting = False
    q_text_lines = []
    lines = text.split("\n")
    for original_line in lines:
        line = original_line.strip()
        # Detect unit
        unit_match = re.match(r"Unit\s*[–-]?\s*(I{1,5}|IV|V)\b", line, re.IGNORECASE)
        if unit_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
                collecting = False
                q_text_lines = []
            roman = unit_match.group(1).upper()
            unit_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
            current_unit = unit_map.get(roman)
            continue
        # Detect part
        part_match = re.match(r"PART\s*[–-]?\s*([A-C])\b", line, re.IGNORECASE)
        if part_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
                collecting = False
                q_text_lines = []
            current_part = part_match.group(1).upper()
            continue
        # Skip irrelevant lines
        if (
            not line
            or re.match(r"CO\d+:", line)
            or re.match(r"Q.NO|QUESTIONS|CO’S|BLOOM|LEVEL", line, re.IGNORECASE)
        ):
            continue
        # Start new question
        start_match = re.match(r"^(\d{1,2})\.\s*(.*)$", line)
        if start_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
            remaining_text = start_match.group(2).strip()
            q_text_lines = [remaining_text] if remaining_text else []
            collecting = True
            continue
        # If collecting, append the line
        if collecting and line:
            q_text_lines.append(line)
    # Flush the last question
    if collecting:
        questions = flush_question(questions, current_unit, current_part, q_text_lines)
    return questions


def flush_question(questions, unit, part, lines):
    if not lines or not unit or not part:
        return questions
    text = " ".join(lines).strip()
    # Extract COx Kx
    cb_match = re.search(r"CO(\d+)\s+K(\d+)(?:\s*Q\.)?", text, re.IGNORECASE)
    if cb_match:
        co = f"CO{cb_match.group(1)}"
        bloom = f"K{cb_match.group(2)}"
        text = text[: cb_match.start()].strip()
    else:
        return questions  # Skip if no CO/Bloom
    questions.append(Question(unit=unit, part=part, text=text, co=co, bloom=bloom))
    return questions






"""import pdfplumber
import re
from question import Question

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
            if page_text:
                text += page_text + "\n"
    return text

def extract_header(text):
    header = {
        "exam_type": "",
        "subject_code": "",
        "subject_name": "",
        "regulation": "",
        "department": "",
        "semester": "",
        "course_outcomes": [],
    }
    
    lines = text.split("\n")
    co_mode = False
    current_co = ""
    in_header = True

    for i, line_raw in enumerate(lines):
        line = line_raw.strip()
        
        if not line:
            continue
        
        # Stop at Unit or PART
        if re.search(r"Unit\s*[–-]\s*[IVX12345]", line, re.IGNORECASE) or "PART" in line.upper():
            in_header = False
            if co_mode and current_co:
                header["course_outcomes"].append(current_co.strip())
            break
        
        if not in_header:
            continue
        
        # Exam Type
        if "CONTINUOUS ASSESSMENT TEST" in line.upper():
            header["exam_type"] = line
        
        # Regulation
        if "Regulations R" in line:
            header["regulation"] = line
        
        # Department
        if "Department" in line:
            header["department"] = line
        
        # Semester
        if "Year" in line and "Semester" in line:
            header["semester"] = line
        
        # Subject Code + Name
        subj_match = re.search(r"(\d{4}[A-Z]{3}\d{3}T|[A-Z]{3}\d{3}T)\s*[-–]?\s*(.+)", line)
        if subj_match:
            header["subject_code"] = subj_match.group(1)
            subject_name = subj_match.group(2).strip()
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                if re.match(r"^CO[1-5]:", next_line) or "Unit" in next_line or "PART" in next_line.upper():
                    break
                subject_name += " " + next_line
                j += 1
            header["subject_name"] = subject_name.strip()
            continue
        
        # Course Outcomes
        if re.match(r"^CO[1-5]:", line):
            if co_mode and current_co:
                header["course_outcomes"].append(current_co.strip())
            co_mode = True
            current_co = line.strip()
        elif co_mode:
            if re.match(r"^CO[1-5]:", line):
                header["course_outcomes"].append(current_co.strip())
                current_co = line.strip()
            else:
                current_co += " " + line.strip()
    
    if co_mode and current_co:
        header["course_outcomes"].append(current_co.strip())
    
    return header

def extract_questions(text):
    questions = []
    current_unit = None
    current_part = None
    collecting = False
    q_text_lines = []
    lines = text.split("\n")
    for original_line in lines:
        line = original_line.strip()
        # Detect unit
        unit_match = re.match(r"Unit\s*[–-]?\s*(I{1,5}|IV|V)\b", line, re.IGNORECASE)
        if unit_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
                collecting = False
                q_text_lines = []
            roman = unit_match.group(1).upper()
            unit_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
            current_unit = unit_map.get(roman)
            continue
        # Detect part
        part_match = re.match(r"PART\s*[–-]?\s*([A-C])\b", line, re.IGNORECASE)
        if part_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
                collecting = False
                q_text_lines = []
            current_part = part_match.group(1).upper()
            continue
        # Skip irrelevant lines
        if (
            not line
            or re.match(r"CO\d+:", line)
            or re.match(r"Q.NO|QUESTIONS|CO’S|BLOOM|LEVEL", line, re.IGNORECASE)
        ):
            continue
        # Start new question
        start_match = re.match(r"^(\d{1,2})\.\s*(.*)$", line)
        if start_match:
            if collecting:
                questions = flush_question(
                    questions, current_unit, current_part, q_text_lines
                )
            remaining_text = start_match.group(2).strip()
            q_text_lines = [remaining_text] if remaining_text else []
            collecting = True
            continue
        # If collecting, append the line
        if collecting and line:
            q_text_lines.append(line)
    # Flush the last question
    if collecting:
        questions = flush_question(questions, current_unit, current_part, q_text_lines)
    return questions

def flush_question(questions, unit, part, lines):
    if not lines or not unit or not part:
        return questions
    text = " ".join(lines).strip()
    # Extract COx Kx
    cb_match = re.search(r"CO(\d+)\s+K(\d+)(?:\s*Q\.)?", text, re.IGNORECASE)
    if cb_match:
        co = f"CO{cb_match.group(1)}"
        bloom = f"K{cb_match.group(2)}"
        text = text[:cb_match.start()].strip()
    else:
        return questions # Skip if no CO/Bloom
    questions.append(Question(unit=unit, part=part, text=text, co=co, bloom=bloom))
    return questions
"""

