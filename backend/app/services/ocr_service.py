import pytesseract
import cv2
import numpy as np
from typing import List, Dict, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        """Initialize Tesseract OCR"""
        # Configure pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust path if needed
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better OCR results"""
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(thresh)
        
        return enhanced
    
    def extract_text_from_image(self, image_path: str) -> List[Dict]:
        """Extract text with bounding boxes from image"""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)

            # Perform OCR using pytesseract
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)

            extracted_data = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > -1:  # Include all detections for debugging
                    bbox = [
                        [data['left'][i], data['top'][i]],
                        [data['left'][i] + data['width'][i], data['top'][i]],
                        [data['left'][i] + data['width'][i], data['top'][i] + data['height'][i]],
                        [data['left'][i], data['top'][i] + data['height'][i]]
                    ]
                    text = data['text'][i].strip()
                    if text:  # Only include non-empty text
                        confidence = data['conf'][i] / 100.0  # Convert to 0-1 scale

                        extracted_data.append({
                            'bbox': bbox,
                            'text': text,
                            'confidence': confidence
                        })

            return extracted_data

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, List[Dict]]:
        """Extract text from all pages of PDF using OCR"""
        import fitz  # PyMuPDF
        import tempfile

        pages_data = {}

        try:
            # Open PDF with PyMuPDF
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Render page to image
                pix = page.get_pixmap(dpi=600)
                img_data = pix.tobytes("png")

                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(img_data)
                    tmp.close()  # Explicitly close the file

                    # Extract text from page image
                    page_data = self.extract_text_from_image(tmp.name)
                    pages_data[page_num + 1] = page_data

                    # Clean up temp file
                    os.unlink(tmp.name)

            doc.close()
            return pages_data

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise