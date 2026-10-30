"""
Offline OCR Engine for Lucknow High Court Typists
Supports Devanagari Hindi + English with advanced preprocessing for WhatsApp photos.
"""
import os
import cv2
import numpy as np
from PIL import Image
try:
    import easyocr
except ImportError:
    easyocr = None
from legal_corrector import clean_ocr_text

# Global singleton reader to avoid re-initializing weights on every request
_OCR_READER = None

def get_ocr_reader():
    global _OCR_READER
    if easyocr is None:
        raise RuntimeError("EasyOCR मॉड्यूल उपलब्ध नहीं है। कृपया AI विज़न मोड का उपयोग करें।")
    if _OCR_READER is None:
        # Initialize offline EasyOCR reader with Hindi and English
        _OCR_READER = easyocr.Reader(['hi', 'en'], gpu=False, verbose=False)
    return _OCR_READER

def preprocess_image(cv_img, deskew=True, contrast_boost=True, denoise=True, rotation=0):
    """
    Applies professional image preprocessing tailored for WhatsApp court document photos.
    """
    # 1. Apply manual rotation if needed
    if rotation == 90:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_CLOCKWISE)
    elif rotation == 180:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_180)
    elif rotation == 270:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Convert to grayscale
    if len(cv_img.shape) == 3:
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv_img

    # 2. Deskew (straighten tilted photos)
    if deskew:
        try:
            # Detect edges and calculate tilt angle
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    # Consider near horizontal lines (-45 to 45 deg)
                    if -45 < angle < 45:
                        angles.append(angle)
                if angles:
                    median_angle = np.median(angles)
                    if abs(median_angle) > 0.5 and abs(median_angle) < 25:
                        h, w = gray.shape
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass # fallback to original if deskew fails

    # 3. Denoise
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, h=8, templateWindowSize=7, searchWindowSize=21)

    # 4. Contrast enhancement using CLAHE
    if contrast_boost:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    return gray

def extract_text_from_image(image_input, rotation=0, apply_enhancement=True) -> tuple[str, str, np.ndarray]:
    """
    Takes an image file path or numpy array/bytes, runs offline OCR, and returns:
    (raw_text, cleaned_legal_text, enhanced_image)
    """
    reader = get_ocr_reader()
    
    # Handle various input formats safely
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    elif isinstance(image_input, Image.Image):
        # Convert PIL Image to OpenCV BGR format
        rgb_img = np.array(image_input.convert("RGB"))
        img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
    elif hasattr(image_input, 'getvalue'): # Streamlit UploadedFile
        bytes_data = image_input.getvalue()
        if not bytes_data and hasattr(image_input, 'seek'):
            image_input.seek(0)
            bytes_data = image_input.read()
        nparr = np.frombuffer(bytes_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif hasattr(image_input, 'read'): # Other file-like stream
        if hasattr(image_input, 'seek'):
            image_input.seek(0)
        bytes_data = image_input.read()
        nparr = np.frombuffer(bytes_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    elif isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        raise ValueError("Unsupported image input type")

    if img is None:
        raise ValueError("फोटो लोड नहीं हो सकी (Image buffer empty or invalid format)")

    # Preprocessing
    if apply_enhancement:
        processed_img = preprocess_image(img, rotation=rotation)
    else:
        if rotation != 0:
            if rotation == 90:
                processed_img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                processed_img = cv2.rotate(img, cv2.ROTATE_180)
            elif rotation == 270:
                processed_img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            else:
                processed_img = img
        else:
            processed_img = img

    # Run EasyOCR
    results = reader.readtext(processed_img, detail=0)
    raw_text = "\n".join(results)
    cleaned_legal_text = clean_ocr_text(results)
    
    return raw_text, cleaned_legal_text, processed_img
