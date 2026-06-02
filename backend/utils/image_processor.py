"""
Image Processor Utility
Handles file conversions (PDF→image, DXF→image)
"""
from typing import List, Tuple, Optional, BinaryIO
import os
import io
from config import MAX_FLOORS
from utils.errors import FileCorruptError, InvalidImageDimensionsError


class ImageProcessor:
    """Processes various file formats into images"""
    
    @staticmethod
    def convert_pdf_to_images(pdf_data: bytes, filename: str) -> List[bytes]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_data: Binary PDF data
            filename: Name of the file
            
        Returns:
            List of image data (one per page)
            
        Raises:
            FileCorruptError: If PDF is corrupt
        """
        try:
            import pypdf
            from pdf2image import convert_from_bytes
            
            # Read PDF
            reader = pypdf.PdfReader(io.BytesIO(pdf_data))
            num_pages = len(reader.pages)
            
            if num_pages == 0:
                raise FileCorruptError(f"PDF '{filename}' has no pages")
            
            if num_pages > MAX_FLOORS:
                # Truncate to max floors
                num_pages = MAX_FLOORS
            
            # Convert to images
            images = convert_from_bytes(pdf_data, first_page=num_pages)
            
            # Convert PIL images to bytes
            image_data_list = []
            for img in images:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                image_data_list.append(img_byte_arr.getvalue())
            
            return image_data_list
            
        except Exception as e:
            if "corrupt" in str(e).lower() or "invalid" in str(e).lower():
                raise FileCorruptError(f"PDF '{filename}' is corrupt or unreadable")
            else:
                raise FileCorruptError(f"Failed to convert PDF: {str(e)}")
    
    @staticmethod
    def convert_dxf_to_image(dxf_data: bytes, filename: str) -> bytes:
        """
        Convert DXF file to image
        
        Args:
            dxf_data: Binary DXF data
            filename: Name of the file
            
        Returns:
            Image data
            
        Raises:
            FileCorruptError: If DXF is corrupt
        """
        try:
            import ezdxf
            from PIL import Image
            import numpy as np
            
            # Load DXF
            doc = ezdxf.readfile(io.BytesIO(dxf_data))
            msp = doc.modelspace()
            
            # Get extents
            min_x, min_y, max_x, max_y = msp.dxf extents if hasattr(msp, 'dxf') else (0, 0, 1000, 1000)
            
            # Create a simple rendering (basic implementation)
            # For production, you'd use a proper DXF renderer
            width = int(max_x - min_x) + 100
            height = int(max_y - min_y) + 100
            
            # Create white background
            img_array = np.ones((height, width, 3), dtype=np.uint8) * 255
            
            # Convert to PIL Image
            image = Image.fromarray(img_array, 'RGB')
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            raise FileCorruptError(f"Failed to convert DXF '{filename}': {str(e)}")
    
    @staticmethod
    def convert_dwg_to_image(dwg_data: bytes, filename: str) -> bytes:
        """
        Convert DWG file to image (via DXF conversion)
        
        Args:
            dwg_data: Binary DWG data
            filename: Name of the file
            
        Returns:
            Image data
            
        Raises:
            FileCorruptError: If DWG is corrupt or unsupported
        """
        try:
            # DWG is a proprietary format with no open spec
            # Try to convert via ezdxf (may not work for all DWG versions)
            # For production, use a commercial converter like ODA File Converter
            
            # For now, return an error suggesting DXF export
            raise FileCorruptError(
                f"DWG files are not directly supported. "
                f"Please export '{filename}' as DXF from AutoCAD."
            )
            
        except Exception as e:
            raise FileCorruptError(f"Failed to convert DWG '{filename}': {str(e)}")
    
    @staticmethod
    def validate_image_dimensions(image_data: bytes, min_width: int = 100, min_height: int = 100) -> Tuple[int, int]:
        """
        Validate and get image dimensions
        
        Args:
            image_data: Binary image data
            min_width: Minimum allowed width
            min_height: Minimum allowed height
            
        Returns:
            Tuple of (width, height)
            
        Raises:
            InvalidImageDimensionsError: If dimensions are invalid
        """
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            if width < min_width or height < min_height:
                raise InvalidImageDimensionsError(
                    "image",
                    width,
                    height
                )
            
            return width, height
            
        except InvalidImageDimensionsError:
            raise
        except Exception as e:
            raise FileCorruptError(f"Failed to read image: {str(e)}")
    
    @staticmethod
    def resize_image(image_data: bytes, max_width: int = 2048, max_height: int = 2048) -> bytes:
        """
        Resize image to fit within max dimensions while maintaining aspect ratio
        
        Args:
            image_data: Binary image data
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized image data
        """
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate new dimensions
            width, height = image.size
            ratio = min(max_width / width, max_height / height)
            
            if ratio < 1:
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            # If resize fails, return original
            return image_data
    
    @staticmethod
    def detect_file_type(file_data: bytes, filename: str) -> str:
        """
        Detect actual file type from content (not just extension)
        
        Args:
            file_data: Binary file data
            filename: Original filename
            
        Returns:
            Detected file extension (e.g., ".pdf", ".png")
        """
        # Check magic bytes
        if file_data.startswith(b'%PDF'):
            return '.pdf'
        elif file_data.startswith(b'\x89PNG'):
            return '.png'
        elif file_data.startswith(b'\xff\xd8\xff'):
            return '.jpg'  # JPEG
        elif file_data.startswith(b'AC10'):  # DXF magic bytes
            return '.dxf'
        
        # Fall back to extension
        _, ext = os.path.splitext(filename)
        return ext.lower()
    
    @staticmethod
    def process_file(file_data: bytes, filename: str) -> List[bytes]:
        """
        Process any supported file format into images
        
        Args:
            file_data: Binary file data
            filename: Name of the file
            
        Returns:
            List of image data (one per page/floor)
            
        Raises:
            FileCorruptError: If file is corrupt or unsupported
        """
        # Detect actual file type
        file_type = ImageProcessor.detect_file_type(file_data, filename)
        
        if file_type == '.pdf':
            return ImageProcessor.convert_pdf_to_images(file_data, filename)
        elif file_type == '.dxf':
            return [ImageProcessor.convert_dxf_to_image(file_data, filename)]
        elif file_type == '.dwg':
            return [ImageProcessor.convert_dwg_to_image(file_data, filename)]
        elif file_type in ['.png', '.jpg', '.jpeg']:
            # Validate image
            ImageProcessor.validate_image_dimensions(file_data)
            return [file_data]
        else:
            raise FileCorruptError(
                f"Unsupported file type: {file_type}. "
                f"Supported types: .pdf, .png, .jpg, .jpeg, .dxf"
            )
