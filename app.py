import os
from datetime import date

import requests
import streamlit as st
from dotenv import load_dotenv

from services.document_formatter import (
    format_as_txt,
    format_as_docx,
    format_as_pdf,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)

DEFAULT_BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LegalEaseAI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "generated_content" not in st.session_state:
    st.session_state.generated_content = ""

if "edited_content" not in st.session_state:
    st.session_state.edited_content = ""

# This is the IMPORTANT state used for downloads.
if "saved_content" not in st.session_state:
    st.session_state.saved_content = ""

if "generated_document_type" not in st.session_state:
    st.session_state.generated_document_type = ""

if "generation_success" not in st.session_state:
    st.session_state.generation_success = False

if "generation_id" not in st.session_state:
    st.session_state.generation_id = 0

if "edit_saved" not in st.session_state:
    st.session_state.edit_saved = False


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 48px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 35px;
    }

    .section-title {
        font-size: 30px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    .download-title {
        font-size: 32px;
        font-weight: 650;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .footer {
        text-align: center;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #dddddd;
        color: #777777;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚖️ LegalEaseAI")

    st.write(
        "AI-assisted legal document drafting."
    )

    st.divider()

    st.markdown("### Backend")

    backend_url = st.text_input(
        "Backend URL",
        value=DEFAULT_BACKEND_URL,
        help="URL where the FastAPI backend is running.",
    )

    if st.button(
        "Check Backend",
        use_container_width=True,
    ):

        try:

            response = requests.get(
                f"{backend_url.rstrip('/')}/health",
                timeout=5,
            )

            if response.status_code == 200:

                st.success(
                    "Backend is running."
                )

            else:

                st.error(
                    f"Backend returned HTTP {response.status_code}."
                )

        except requests.exceptions.RequestException as exc:

            st.error(
                "Could not connect to backend."
            )

            st.caption(
                str(exc)
            )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚖️ LegalEaseAI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        AI-assisted legal document drafting.
        Enter the information below and generate a structured legal document.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INPUT SECTION
# ============================================================

st.markdown(
    '<div class="section-title">Create Legal Document</div>',
    unsafe_allow_html=True,
)


# ============================================================
# DOCUMENT TYPE
# ============================================================

document_types = [
    "Rental Agreement",
    "Employment Agreement",
    "Non-Disclosure Agreement",
    "Service Agreement",
    "Freelance Contract",
    "Lease Agreement",
    "Sale Agreement",
    "Partnership Agreement",
    "Loan Agreement",
    "General Agreement",
    "Other",
]

document_type = st.selectbox(
    "Document Type",
    document_types,
)


# ============================================================
# PARTIES
# ============================================================

parties = st.text_area(
    "Parties",
    value="",
    height=130,
    placeholder=(
        "Enter the parties involved.\n\n"
        "Example:\n"
        "Party 1: [Name], [Role]\n"
        "Party 2: [Name], [Role]"
    ),
    help="Enter the names and roles of all parties.",
)


# ============================================================
# TERMS
# ============================================================

terms = st.text_area(
    "Terms and Conditions",
    value="",
    height=250,
    placeholder=(
        "Enter the terms and conditions.\n\n"
        "You can enter each clause on a separate line.\n\n"
        "Example:\n"
        "Monthly payment shall be made on or before the 5th day of each month.\n"
        "The property shall be maintained in good condition.\n"
        "Either party may terminate the agreement with 30 days written notice."
    ),
    help="Enter the clauses and conditions.",
)


# ============================================================
# EFFECTIVE DATE
# ============================================================

effective_date = st.text_input(
    "Effective Date",
    value="",
    placeholder="YYYY-MM-DD",
    help="Enter the effective date in YYYY-MM-DD format.",
)


# ============================================================
# GENERATE BUTTON
# ============================================================

st.markdown("")

generate_clicked = st.button(
    "⚖️ Generate Legal Document",
    type="primary",
    use_container_width=True,
)


# ============================================================
# GENERATE DOCUMENT
# ============================================================

if generate_clicked:

    if not parties.strip():

        st.error(
            "Please enter the parties involved."
        )

        st.stop()

    if not terms.strip():

        st.error(
            "Please enter the terms and conditions."
        )

        st.stop()

    if not effective_date.strip():

        st.error(
            "Please enter the effective date."
        )

        st.stop()

    try:

        date.fromisoformat(
            effective_date.strip()
        )

    except ValueError:

        st.error(
            "Please enter the effective date in YYYY-MM-DD format."
        )

        st.stop()

    payload = {
        "document_type": document_type,
        "parties": parties.strip(),
        "terms": terms.strip(),
        "effective_date": effective_date.strip(),
    }

    with st.spinner(
        "Generating your legal document..."
    ):

        try:

            response = requests.post(
                f"{backend_url.rstrip('/')}/generate",
                json=payload,
                timeout=180,
            )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to the FastAPI backend."
            )

            st.info(
                "Make sure the backend is running with:"
            )

            st.code(
                "python -m uvicorn main:app --host 127.0.0.1 --port 8000"
            )

            st.stop()

        except requests.exceptions.Timeout:

            st.error(
                "The backend took too long to respond."
            )

            st.stop()

        except requests.exceptions.RequestException as exc:

            st.error(
                f"Request failed: {exc}"
            )

            st.stop()

    if response.status_code != 200:

        st.error(
            f"Backend returned HTTP {response.status_code}."
        )

        try:

            st.code(
                str(response.json())
            )

        except Exception:

            st.code(
                response.text
            )

        st.stop()

    try:

        result = response.json()

    except ValueError:

        st.error(
            "Backend returned invalid JSON."
        )

        st.stop()

    if not result.get("success", True):

        st.error(
            result.get(
                "message",
                "Document generation failed.",
            )
        )

        st.stop()

    generated_content = result.get(
        "content",
        "",
    )

    if not generated_content:

        st.error(
            "The backend did not return any document content."
        )

        st.stop()

    # --------------------------------------------------------
    # Store NEW document
    # --------------------------------------------------------

    st.session_state.generated_content = generated_content

    st.session_state.edited_content = generated_content

    # IMPORTANT:
    # The newly generated document is also the current
    # downloadable version until the user edits it.
    st.session_state.saved_content = generated_content

    st.session_state.generated_document_type = result.get(
        "document_type",
        document_type,
    )

    st.session_state.generation_id += 1

    st.session_state.generation_success = True

    st.session_state.edit_saved = False

    st.success(
        "Legal document generated successfully!"
    )

    # Rerun so the editor receives the new document cleanly.
    st.rerun()


# ============================================================
# GENERATED DOCUMENT SECTION
# ============================================================

if st.session_state.generation_success:

    st.divider()

    st.markdown(
        '<div class="section-title">Generated Document</div>',
        unsafe_allow_html=True,
    )

    generated_type = (
        st.session_state.generated_document_type
        or document_type
    )

    st.subheader(
        generated_type
    )

    st.write(
        "Edit the document below, then click "
        "**Save Edited Document** before downloading."
    )

    # --------------------------------------------------------
    # EDITOR
    # --------------------------------------------------------

    editor_key = (
        f"document_editor_{st.session_state.generation_id}"
    )

    edited_content = st.text_area(
        "Edit your document",
        value=st.session_state.edited_content,
        height=600,
        key=editor_key,
    )

    # --------------------------------------------------------
    # Save edited document button
    # --------------------------------------------------------

    st.markdown("")

    save_clicked = st.button(
        "💾 Save Edited Document",
        type="primary",
        use_container_width=True,
        key=f"save_edits_{st.session_state.generation_id}",
    )

    if save_clicked:

        if not edited_content.strip():

            st.error(
                "The document cannot be empty."
            )

        else:

            # Save exactly what is currently in the editor.
            st.session_state.edited_content = edited_content

            st.session_state.saved_content = edited_content

            st.session_state.edit_saved = True

            st.success(
                "Your edited document has been saved. "
                "The download buttons now use the edited version."
            )

    # --------------------------------------------------------
    # Always keep the latest editor value in session state.
    # This is useful even before pressing Save.
    # --------------------------------------------------------

    st.session_state.edited_content = edited_content


    # ========================================================
    # DOWNLOAD SECTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="download-title">⬇️ Download</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.edit_saved:

        st.success(
            "Downloads contain your saved edited version."
        )

    else:

        st.info(
            "If you changed the document above, click "
            "'Save Edited Document' before downloading."
        )


    # --------------------------------------------------------
    # THIS IS THE IMPORTANT PART
    #
    # Downloads use saved_content, NOT generated_content.
    # --------------------------------------------------------

    downloadable_content = (
        st.session_state.saved_content
    )

    # --------------------------------------------------------
    # TXT
    # --------------------------------------------------------

    try:

        txt_data = format_as_txt(
            downloadable_content
        )

        st.download_button(
            label="📄 Download TXT",
            data=txt_data,
            file_name="legal_document.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"download_txt_{st.session_state.generation_id}",
        )

    except Exception as exc:

        st.error(
            "TXT file could not be prepared."
        )

        st.exception(exc)


    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    try:

        docx_data = format_as_docx(
            downloadable_content,
            generated_type,
        )

        st.download_button(
            label="📝 Download DOCX",
            data=docx_data,
            file_name="legal_document.docx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
            key=f"download_docx_{st.session_state.generation_id}",
        )

    except Exception as exc:

        st.error(
            "DOCX file could not be prepared."
        )

        st.exception(exc)


    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    try:

        pdf_data = format_as_pdf(
            downloadable_content,
            generated_type,
        )

        st.download_button(
            label="📕 Download PDF",
            data=pdf_data,
            file_name="legal_document.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_pdf_{st.session_state.generation_id}",
        )

    except Exception as exc:

        st.error(
            "PDF file could not be prepared."
        )

        st.exception(exc)


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        LegalEaseAI — AI-assisted legal document drafting.
        Generated documents should be reviewed by a qualified
        legal professional before use.
    </div>
    """,
    unsafe_allow_html=True,
)