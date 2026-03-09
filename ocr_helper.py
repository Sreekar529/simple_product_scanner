import cv2
import easyocr
import re
import numpy as np


def initialize_ocr():
    # Create the EasyOCR reader (English only for now)
    return easyocr.Reader(["en"], gpu=False)


def preprocess_image(image):
    # Basic image cleanup before OCR:
    # grayscale + contrast + threshold usually gives better text
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Boost local contrast a bit
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # Turn into a black/white image
    _, thresh = cv2.threshold(
        contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh


def extract_text(reader, image, use_preprocessing=True):
    # Run OCR and return:
    # - all text joined into a string
    # - average confidence across detections
    if use_preprocessing:
        processed = preprocess_image(image)
        results = reader.readtext(processed)
    else:
        results = reader.readtext(image)

    full_text = " ".join(res[1] for res in results)
    conf = sum(res[2] for res in results) / len(results) if results else 0
    return full_text, conf


def extract_numbers(text):
    # Pull out 8–14 digit sequences that could be barcodes (EAN/UPC style)
    return re.findall(r"\b\d{8,14}\b", text)


def find_important_words(text):
    # Pull out "interesting" words that might be part of the product name
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Take words with 2+ alphanumeric chars (captures things like "v29")
    words = re.findall(r"\b[A-Za-z0-9]{2,}\b", text)

    # Make sure we explicitly keep known brand names if they appear anywhere
    known_brands = (
        "vivo",
        "samsung",
        "iphone",
        "oneplus",
        "redmi",
        "realme",
        "google",
        "motorola",
        "oppo",
        "iqoo",
    )
    for brand in known_brands:
        if re.search(rf"\b{re.escape(brand)}\b", text, flags=re.IGNORECASE):
            words.append(brand)
    # Throw away generic label words
    stop_words = {
        "ingredients",
        "nutrition",
        "facts",
        "total",
        "sugar",
        "weight",
        "serving",
        "servings",
        "amount",
        "brand",
        "barcode",
        "label",
        "category",
        "top",
        "results",
        "product",
        "trending",
    }
    return [w for w in words if w.lower() not in stop_words]


