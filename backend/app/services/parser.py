# =============================================================================
# CV Parser Service
# Extracts and parses structured sections from CV files (PDF/DOCX)
# =============================================================================

from io import BytesIO
from pathlib import Path
import re

import fitz  # PyMuPDF
from docx import Document as DocxDocument

# Supported file types
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# Section header patterns for detection (case-insensitive, regex)
SECTION_PATTERNS = {
    "experience": [
        r"experience", r"work\s*experience", r"employment",
        r"work\s*history", r"professional\s*experience", r"career"
    ],
    "education": [
        r"education", r"academic", r"qualifications",
        r"degrees?", r"university", r"college"
    ],
    "skills": [
        r"skills", r"competencies", r"expertise", r"technologies",
        r"technical\s*skills", r"proficiencies", r"abilities"
    ],
    "projects": [
        r"projects?", r"portfolio", r"personal\s*projects?",
        r"academic\s*projects?", r"professional\s*projects?"
    ],
}


# -----------------------------------------------------------------------------
# Private Helper Functions
# -----------------------------------------------------------------------------


def _build_section_regex() -> dict[str, re.Pattern]:
    """Compile regex patterns for section detection."""
    return {
        section: re.compile(
            rf"^\s*({'|'.join(patterns)})\s*[:\-]?\s*$",
            re.IGNORECASE | re.MULTILINE
        )
        for section, patterns in SECTION_PATTERNS.items()
    }


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file using PyMuPDF.

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Concatenated text from all pages, separated by newlines
    """
    text_parts = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text content from a DOCX file using python-docx.

    Args:
        file_bytes: Raw bytes of the DOCX file

    Returns:
        Concatenated text from all paragraphs, separated by newlines
    """
    doc = DocxDocument(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def _parse_sections(text: str) -> dict[str, str]:
    """
    Parse extracted text and split into resume sections.

    Args:
        text: Full extracted text from CV

    Returns:
        Dictionary with section names as keys and their content as values.
        Unmatched content goes into 'other' key.
    """
    sections = {section: [] for section in SECTION_PATTERNS.keys()}
    sections["other"] = []
    section_order = []

    lines = text.split("\n")
    section_patterns = _build_section_regex()
    current_section = "other"

    for line in lines:
        matched_section = None

        # Check if line is a section header
        for section, pattern in section_patterns.items():
            if pattern.match(line.strip()):
                matched_section = section
                break

        if matched_section:
            # Start tracking a new section
            if matched_section != current_section:
                current_section = matched_section
                if matched_section not in section_order:
                    section_order.append(matched_section)
        else:
            # Add content to current section
            if line.strip():
                sections[current_section].append(line.strip())

    # Build final dictionary preserving section order
    result = {}
    for section in list(section_order) + ["other"]:
        if section != "other" and sections[section]:
            result[section] = "\n".join(sections[section])
        elif section == "other" and sections["other"]:
            result["other"] = "\n".join(sections["other"])

    return result


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def parse_cv_file(file_path: str) -> dict[str, str]:
    """
    Detect file type from path, extract text, and parse into sections.

    Args:
        file_path: Absolute or relative path to PDF or DOCX file

    Returns:
        Dictionary with section names (experience, education, skills, projects)
        as keys and extracted text content as values.

    Example:
        {
            "experience": "Software Engineer at Company...",
            "education": "BS Computer Science...",
            "skills": "Python, JavaScript...",
            "projects": "Built a REST API...",
            "other": "Any unmatched content..."
        }

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If file type is not supported (not pdf/docx)
    """
    path = Path(file_path)

    # Validate file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Detect file type from extension
    file_extension = path.suffix.lower().lstrip(".")
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_extension}. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file bytes
    file_bytes = path.read_bytes()

    # Extract raw text based on file type
    if file_extension == "pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    else:  # docx
        raw_text = _extract_text_from_docx(file_bytes)

    # Parse into structured sections
    return _parse_sections(raw_text)


def parse_cv_bytes(file_bytes: bytes, file_type: str) -> dict[str, str]:
    """
    Extract and parse CV sections from file bytes.

    Args:
        file_bytes: Raw bytes of the CV file
        file_type: File type string ('pdf' or 'docx')

    Returns:
        Dictionary with section names as keys and extracted text as values.
        See parse_cv_file for example return value.

    Raises:
        ValueError: If file type is not 'pdf' or 'docx'
    """
    file_type = file_type.lower().lstrip(".")
    if file_type not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {file_type}. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Extract raw text based on file type
    if file_type == "pdf":
        raw_text = _extract_text_from_pdf(file_bytes)
    else:  # docx
        raw_text = _extract_text_from_docx(file_bytes)

    # Parse into structured sections
    return _parse_sections(raw_text)
