# Implementation Plan - Expanding File Support and Increasing Size Limit

The goal is to enable processing for PDF, JPG, and PNG files in addition to DXF, and to increase the maximum upload size beyond 50MB.

## User Review Required

> [!IMPORTANT]
> I need to verify which libraries are preferred for PDF (e.g., PyMuPDF, pdf2image) and Image (e.g., Pillow, OpenCV) processing if they aren't already in the project.

## Proposed Changes

### Backend

#### `app.py` or configuration files
- Identify the upload size limit (likely a Flask or FastAPI config) and increase it.
- Ensure the file upload endpoint accepts PDF, JPG, and PNG extensions.

#### `backend/blueprint_logic.py`
- Analyze the logic for DXF processing.
- Implement or fix the handlers for PDF, JPG, and PNG.
- This might involve:
    - Converting images/PDFs to a format suitable for the core logic (e.g., OCR or line detection).
    - Integrating an LLM or specialized vision model if the "blueprint reading" involves analysis.

## Verification Plan

### Automated Tests
- Upload a PDF file > 50MB (if possible in test environment) or mock the size check.
- Test processing of small PDF, JPG, and PNG files.

### Manual Verification
- Use the frontend to upload various file types and check the output.
