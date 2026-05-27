# =============================================================================
# CV Upload Router
# Handles CV file uploads (PDF/DOCX) and text extraction
# =============================================================================

from fastapi import APIRouter, UploadFile, File, HTTPException
from io import BytesIO
import fitz  # PyMuPDF
from docx import Document as DocxDocument

# Create router with prefix for all CV-related endpoints
router = APIRouter(prefix="/api/cv", tags=["cv"])

# Supported file types for CV uploads
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# Maximum allowed file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# -----------------------------------------------------------------------------
# Text Extraction Functions
# -----------------------------------------------------------------------------


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text content from a PDF file using PyMuPDF.

    Args:
        file_bytes: Raw bytes of the PDF file

    Returns:
        Concatenated text from all pages, separated by newlines
    """
    text_parts = []
    # Open PDF from bytes stream (filetype="pdf" ensures correct parsing)
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # Iterate through each page and extract text
    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text content from a DOCX file using python-docx.

    Args:
        file_bytes: Raw bytes of the DOCX file

    Returns:
        Concatenated text from all paragraphs, separated by newlines
    """
    doc = DocxDocument(BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------


@router.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload a CV file (PDF or DOCX) and receive the extracted text.

    Args:
        file: Uploaded file (PDF or DOCX format)

    Returns:
        Dictionary containing:
            - filename: Original filename
            - file_type: File extension (pdf/docx)
            - text: Extracted text content
            - text_length: Character count of extracted text

    Raises:
        HTTPException 413: If file exceeds 10MB size limit
        HTTPException 400: If file type is not PDF or DOCX
        HTTPException 422: If text extraction fails or no text found
    """
    # Step 1: Validate file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    # Step 2: Validate file extension
    file_extension = file.filename.split(".")[-1].lower() if file.filename else ""
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Step 3: Read file bytes from upload stream
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # Step 4: Extract text based on file type
    try:
        if file_extension == "pdf":
            extracted_text = extract_text_from_pdf(file_bytes)
        else:  # docx
            extracted_text = extract_text_from_docx(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract text: {str(e)}"
        )

    # Step 5: Validate that text was actually extracted
    if not extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the file."
        )

    # Step 6: Return successful response with extracted data
    return {
        "filename": file.filename,
        "file_type": file_extension,
        "text": extracted_text,
        "text_length": len(extracted_text)
    }
