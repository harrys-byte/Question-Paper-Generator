# app.py – Final Streamlit Question Paper Generator (Individual Regenerate + Scaling)

import streamlit as st
import os
import zipfile
import tempfile
import io
import time
from datetime import datetime

# Your existing imports — unchanged
from question import Question
from extract_gen_plain_qb import extract_text_from_pdf as extract_plain, create_plain_text_structured_pdf, course_outcomes
from extract_qb import extract_text_from_pdf, extract_header, extract_questions
from cat_rules import generate_cat1_paper, generate_cat2_paper, generate_endsem_paper
from generate_pdf1 import generate_pdf, generate_pdf_endsem

# Initialize session state
if "generated_pdfs" not in st.session_state:
    st.session_state.generated_pdfs = []  # List of (version_num, filename, bytes)
if "results_generated" not in st.session_state:
    st.session_state.results_generated = False

st.set_page_config(page_title="Question Paper Generator", layout="wide")
st.title("📝 Question Paper Generator")
st.markdown("### Generate multiple versions with individual regenerate option")

# === INPUT SECTION (Larger Font Size) ===
st.subheader("**Enter Paper Details**", anchor=False)  # Bold subheader

col1, col2 = st.columns(2)
with col1:
    exam_type = st.selectbox(
        "**Exam Type**",
        ["cat1", "cat2", "endsem"],
        format_func=lambda x: x.upper(),
        key="exam_type",
    )
    month_year = st.text_input(
        "**Month and Year** (e.g., December 2025)",
        value="December 2025",
        key="month_year",
        help="Enter the exam month and year"
    )

with col2:
    branch = st.text_input(
        "**Branch** (e.g., IT)",
        value="IT",
        key="branch",
    )
    qcode = st.text_input(
        "**Question Paper Code** (e.g., 2311ITC301T)",
        value="2311ITC301T",
        key="qcode",
    )

# Permission message for End Semester
if exam_type == "endsem":
    tallow = st.text_input(
        "**Permission Message** (e.g., 'Calc, Log Book are allowed')",
        value="Calc, Log Book are allowed",
        key="tallow"
    )

# Larger, clearer slider with visible number marks
num_versions = st.slider(
    "**Number of different versions to generate**",
    min_value=1,
    max_value=5,
    value=1,
    step=1,
    format="%d",
    key="num_versions",
    help="Drag to select 1 to 5 versions"
)

# === FILE UPLOAD ===
st.subheader("Upload Question Bank PDFs")

uploaded_files = []
if exam_type in ["cat1", "cat2"]:
    uploaded_file = st.file_uploader(f"Upload {exam_type.upper()} Question Bank PDF", type="pdf", key="upload_single")
    if uploaded_file:
        uploaded_files = [uploaded_file]
else:  # endsem
    col1, col2 = st.columns(2)
    with col1:
        cat1_file = st.file_uploader("Upload CAT-1 PDF", type="pdf", key="upload_cat1")
    with col2:
        cat2_file = st.file_uploader("Upload CAT-2 PDF", type="pdf", key="upload_cat2")
    if cat1_file and cat2_file:
        uploaded_files = [cat1_file, cat2_file]

# === GENERATE / REGENERATE ALL BUTTON ===
button_label = "Regenerate All Versions" if st.session_state.results_generated else f"Generate {num_versions} Version{'s' if num_versions > 1 else ''}"
if st.button(button_label, type="primary", use_container_width=True):
    required = 1 if exam_type in ["cat1", "cat2"] else 2
    if len(uploaded_files) != required:
        st.error(f"Please upload {required} PDF{'s' if required > 1 else ''}.")
    else:
        with st.spinner(f"Generating {num_versions} version{'s' if num_versions > 1 else ''}..."):
            st.session_state.generated_pdfs = []
            progress_bar = st.progress(0)

            for version in range(1, num_versions + 1):
                progress_bar.progress((version - 1) / num_versions)

                with tempfile.TemporaryDirectory() as tmpdir:
                    pdf_paths = []
                    for i, uploaded in enumerate(uploaded_files):
                        temp_path = os.path.join(tmpdir, f"input_v{version}_{i}.pdf")
                        with open(temp_path, "wb") as f:
                            f.write(uploaded.getvalue())
                        pdf_paths.append(temp_path)

                    output_filename = f"{exam_type.upper()}_V{version}.pdf"
                    output_path = os.path.join(tmpdir, output_filename)

                    try:
                        if exam_type in ["cat1", "cat2"]:
                            plain_pdf = create_plain_text_structured_pdf(pdf_paths[0], os.path.join(tmpdir, "plain.pdf"))
                            text = extract_text_from_pdf(plain_pdf)
                            header = extract_header(text)
                            questions = extract_questions(text)
                            cos = course_outcomes(pdf_paths[0])

                            selected = generate_cat1_paper(questions) if exam_type == "cat1" else generate_cat2_paper(questions)

                            generate_pdf(
                                header=header,
                                selected_questions=selected,
                                branch=branch,
                                qcode=qcode,
                                output_path=output_path,
                                cos=cos,
                                month_year=month_year,
                                exam_type=exam_type
                            )

                        else:  # endsem
                            plain1 = create_plain_text_structured_pdf(pdf_paths[0], os.path.join(tmpdir, "plain1.pdf"))
                            plain2 = create_plain_text_structured_pdf(pdf_paths[1], os.path.join(tmpdir, "plain2.pdf"))

                            text1 = extract_text_from_pdf(plain1)
                            text2 = extract_text_from_pdf(plain2)

                            header = extract_header(text1)
                            header["exam_type"] = "END SEMESTER EXAMINATION"

                            cos = course_outcomes(pdf_paths[0])
                            if not cos:
                                cos = course_outcomes(pdf_paths[1])

                            questions = extract_questions(text1) + extract_questions(text2)
                            selected = generate_endsem_paper(questions)

                            generate_pdf_endsem(
                                header=header,
                                selected_questions=selected,
                                branch=branch,
                                qcode=qcode,
                                output_path=output_path,
                                cos=cos,
                                month_year=month_year,
                                exam_type=exam_type,
                                tallow=tallow
                            )

                        with open(output_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.session_state.generated_pdfs.append((version, output_filename, pdf_bytes))

                    except Exception as e:
                        st.error(f"Version {version} failed: {str(e)}")

            progress_bar.progress(1.0)

        st.session_state.results_generated = True
        st.rerun()

# === DISPLAY RESULTS WITH INDIVIDUAL REGENERATE (Visually Appealing) ===
if st.session_state.results_generated and st.session_state.generated_pdfs:
    st.markdown("---")
    st.success(f"Generated {len(st.session_state.generated_pdfs)} version{'s' if len(st.session_state.generated_pdfs) > 1 else ''}!")

    # Responsive grid with cards
    cols = st.columns(len(st.session_state.generated_pdfs))

    # Temporary message placeholder
    regen_placeholder = st.empty()

    for idx, (version_num, filename, pdf_bytes) in enumerate(st.session_state.generated_pdfs):
        with cols[idx]:
            with st.container():
                st.markdown(f"**Version {version_num}**")
                st.download_button(
                    label=f"Download {filename}",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_v{version_num}"
                )
                if st.button(f"Regenerate Version {version_num}", use_container_width=True, key=f"regen_v{version_num}"):
                    with st.spinner(f"Regenerating Version {version_num}..."):
                        with tempfile.TemporaryDirectory() as tmpdir:
                            pdf_paths = []
                            for i, uploaded in enumerate(uploaded_files):
                                temp_path = os.path.join(tmpdir, f"input_regen_{i}.pdf")
                                with open(temp_path, "wb") as f:
                                    f.write(uploaded.getvalue())
                                pdf_paths.append(temp_path)

                            output_path = os.path.join(tmpdir, filename)

                            try:
                                if exam_type in ["cat1", "cat2"]:
                                    plain_pdf = create_plain_text_structured_pdf(pdf_paths[0], os.path.join(tmpdir, "plain.pdf"))
                                    text = extract_text_from_pdf(plain_pdf)
                                    header = extract_header(text)
                                    questions = extract_questions(text)
                                    cos = course_outcomes(pdf_paths[0])

                                    selected = generate_cat1_paper(questions) if exam_type == "cat1" else generate_cat2_paper(questions)

                                    generate_pdf(
                                        header=header,
                                        selected_questions=selected,
                                        branch=branch,
                                        qcode=qcode,
                                        output_path=output_path,
                                        cos=cos,
                                        month_year=month_year,
                                        exam_type=exam_type
                                    )

                                else:
                                    plain1 = create_plain_text_structured_pdf(pdf_paths[0], os.path.join(tmpdir, "plain1.pdf"))
                                    plain2 = create_plain_text_structured_pdf(pdf_paths[1], os.path.join(tmpdir, "plain2.pdf"))

                                    text1 = extract_text_from_pdf(plain1)
                                    text2 = extract_text_from_pdf(plain2)

                                    header = extract_header(text1)
                                    header["exam_type"] = "END SEMESTER EXAMINATION"

                                    cos = course_outcomes(pdf_paths[0])
                                    if not cos:
                                        cos = course_outcomes(pdf_paths[1])

                                    questions = extract_questions(text1) + extract_questions(text2)
                                    selected = generate_endsem_paper(questions)

                                    generate_pdf_endsem(
                                        header=header,
                                        selected_questions=selected,
                                        branch=branch,
                                        qcode=qcode,
                                        output_path=output_path,
                                        cos=cos,
                                        month_year=month_year,
                                        exam_type=exam_type,
                                        tallow=tallow
                                    )

                                with open(output_path, "rb") as f:
                                    new_bytes = f.read()

                                # Update only this version
                                st.session_state.generated_pdfs[idx] = (version_num, filename, new_bytes)

                            except Exception as e:
                                st.error(f"Regeneration failed: {str(e)}")

                    # After regeneration completes → show success message for 3 seconds
                    regen_placeholder.success(f"Version {version_num} regenerated successfully!")
                    time.sleep(1.5)
                    regen_placeholder.empty()

                    st.rerun()
                    

    # === ZIP + CLEAR BUTTONS (Same Style, ZIP Above Clear, Centered) ===
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # ZIP Button
        if len(st.session_state.generated_pdfs) > 1:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for _, name, pdf_bytes in st.session_state.generated_pdfs:
                    zipf.writestr(name, pdf_bytes)
            zip_buffer.seek(0)

            # Track if user just clicked download
            if "zip_download_clicked" not in st.session_state:
                st.session_state.zip_download_clicked = False

            # Show "DOWNLOADING ASSETS..." for 3 seconds after click
            if st.session_state.zip_download_clicked:
                st.download_button(
                    label="DOWNLOADING ASSETS...",
                    data=zip_buffer,
                    file_name=f"{exam_type.upper()}_All_Versions.zip",
                    mime="application/zip",
                    use_container_width=True,
                    type="secondary",
                    disabled=True,
                    key="zip_downloading"
                )
                # Auto-reset after seconds
                time.sleep(1.25)
                st.session_state.zip_download_clicked = False
                st.rerun()

            else:
                # Normal state
                if st.download_button(
                    label="DOWNLOAD ALL VERSIONS AS ZIP",
                    data=zip_buffer,
                    file_name=f"{exam_type.upper()}_All_Versions.zip",
                    mime="application/zip",
                    use_container_width=True,
                    type="secondary",
                    key="zip_normal"
                ):
                    # User clicked — trigger downloading state
                    st.session_state.zip_download_clicked = True
                    st.rerun()

        # Clear Button (completely independent)
        if st.button("CLEAR ALL RESULTS & START NEW", type="primary", use_container_width=True):
            st.session_state.generated_pdfs = []
            st.session_state.results_generated = False
            if "zip_download_clicked" in st.session_state:
                st.session_state.zip_download_clicked = False
            st.rerun()

st.markdown("---")
st.caption("Question Paper Generator • Professional • Multi-Version • Individual Regenerate")