"""
File Validation Service
Validates uploaded files according to the validation chain
"""
from typing import Optional
from fastapi import UploadFile
import os
from config import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_TYPES,
    MAX_FLOORS,
    MIN_IMAGE_DIMENSION
)
from utils.errors import (
    ValidationResult,
    FileMissingError,
    InvalidFilenameError,
    UnsupportedFormatError,
    FileTooLargeError,
    FileCorruptError,
    EmptyPDFError,
    InvalidImageDimensionsError
)


class ValidationResult:
    """Result of file validation"""
    def __init__(
        self,
        is_valid: bool,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[dict] = None
    ):
        self.is_valid = is_valid
        self.error_code = error_code
        self.error_message = error_message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "details": self.details
        }


class FileValidator:
    """Validates uploaded files according to the validation chain"""
    
    @staticmethod
    def validate(file: UploadFile) -> ValidationResult:
        """
        Validate file in exact order. Return the FIRST error found.
        Never expose raw exceptions to the client.
        
        Validation chain:
        1. file is None or empty
        2. filename has no extension
        3. extension not in SUPPORTED_TYPES
        4. file size > MAX_FILE_SIZE_MB
        5. file content unreadable/corrupt
        6. PDF has 0 pages
        7. Image dimensions < 100x100px
        """
        
        # 1. Check if file is None or empty
        if file is None:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_MISSING",
                error_message="No file was provided"
            )
        
        if file.filename is None or file.filename == "":
            return ValidationResult(
                is_valid=False,
                error_code="FILE_MISSING",
                error_message="File has no filename"
            )
        
        # 2. Check if filename has extension
        filename = file.filename
        _, ext = os.path.splitext(filename)
        
        if not ext:
            return ValidationResult(
                is_valid=False,
                error_code="INVALID_FILENAME",
                error_message=f"File '{filename}' has no extension",
                details={"filename": filename}
            )
        
        # 3. Check if extension is supported
        if ext.lower() not in SUPPORTED_TYPES:
            return ValidationResult(
                is_valid=False,
                error_code="UNSUPPORTED_FORMAT",
                error_message=f"File format '{ext}' is not supported",
                details={
                    "filename": filename,
                    "extension": ext,
                    "supported_types": SUPPORTED_TYPES
                }
            )
        
        # 4. Check file size
        # Note: We need to read the file to get size, but we'll do it carefully
        file_size = 0
        try:
            # Read file content to get size
            content = file.file.read()
            file_size = len(content)
            file.file.seek(0)  # Reset file pointer
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_CORRUPT",
                error_message=f"File '{filename}' is corrupt or unreadable",
                details={"filename": filename, "error": str(e)}
            )
        
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                error_code="FILE_TOO_LARGE",
                error_message=f"File '{filename}' is too large ({size_mb:.2f}MB)",
                details={
                    "filename": filename,
                    "max_size_mb": MAX_FILE_SIZE_MB,
                    "actual_size_mb": size_mb
                }
            )
        
        # 5. Check if file content is readable (basic check)
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_CORRUPT",
                error_message=f"File '{filename}' is empty",
                details={"filename": filename}
            )
        
        # 6-7. Format-specific checks
        if ext.lower() == ".pdf":
            return FileValidator._validate_pdf(file, filename)
        elif ext.lower() in [".png", ".jpg", ".jpeg"]:
            return FileValidator._validate_image(file, filename)
        elif ext.lower() in [".dxf", ".dwg"]:
            # DXF/DWG files are handled by the image processor
            # Basic validation only here
            return ValidationResult(is_valid=True)
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def _validate_pdf(file: UploadFile, filename: str) -> ValidationResult:
        """Validate PDF file"""
        try:
            import pypdf
            reader = pypdf.PdfReader(file.file)
            
            if len(reader.pages) == 0:
                return ValidationResult(
                    is_valid=False,
                    error_code="EMPTY_PDF",
                    error_message=f"PDF '{filename}' has no pages",
                    details={"filename": filename}
                )
            
            if len(reader.pages) > MAX_FLOORS:
                return ValidationResult(
                    is_valid=False,
                    error_code="TOO_MANY_PAGES",
                    error_message=f"PDF has {len(reader.pages)} pages. Maximum allowed is {MAX_FLOORS}.",
                    details={
                        "filename": filename,
                        "page_count": len(reader.pages),
                        "max_floors": MAX_FLOORS
                    }
                )
            
            file.file.seek(0)  # Reset file pointer
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_CORRUPT",
                error_message=f"PDF '{filename}' is corrupt or unreadable",
                details={"filename": filename, "error": str(e)}
            )
    
    @staticmethod
    def _validate_image(file: UploadFile, filename: str) -> ValidationResult:
        """Validate image file"""
        try:
            from PIL import Image
            image = Image.open(file.file)
            width, height = image.size
            
            # Check for minimum dimensions
            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                return ValidationResult(
                    is_valid=False,
                    error_code="IMAGE_TOO_SMALL",
                    error_message=f"Image '{filename}' has invalid dimensions ({width}x{height}). Minimum is {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}.",
                    details={
                        "filename": filename,
                        "width": width,
                        "height": height,
                        "min_dimension": MIN_IMAGE_DIMENSION
                    }
                )
            
            file.file.seek(0)  # Reset file pointer
            return ValidationResult(is_valid=True)
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_code="FILE_CORRUPT",
                error_message=f"Image '{filename}' is corrupt or unreadable",
                details={"filename": filename, "error": str(e)}
            )
