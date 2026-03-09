# OCR-Based Product Information Scanner

This is a small Python project that uses OCR to scan product labels from images and then shows product details.  
It looks up products in a MongoDB database and, when possible, pulls ingredients and nutrition facts from the Open Food Facts API.

## What it does
- **Scans images**: Uses EasyOCR to read text and barcodes from product photos.
- **Cleans up images**: Uses OpenCV (grayscale + contrast + threshold) so OCR works better.
- **Looks up data**: Uses MongoDB to find matching products and popularity/category info.
- **Fetches food details**: Uses Open Food Facts to get ingredients and nutrition (only by barcode).
- **Web Interface**: Uses Streamlit for a simple web UI.

## Tech Stack
- **Language**: Python 3.10
- **OCR**: EasyOCR , simple and easy to use
- **Computer Vision**: OpenCV (for image preprocessing)
- **Database**: MongoDB (PyMongo)
- **API**: Open Food Facts API
- **UI**: Streamlit

## Getting Started

### 1. Install dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```
Or you can use uv to install dependencies:
```bash
uv add numpy easyocr opencv-python pymongo pillow requests openfoodfacts streamlit
```
Note : uv is a lot faster than pip and it also installs dependencies automatically. 
### 2. Run the app
Start the Streamlit server:
```bash
streamlit run app.py
```

### 3. Usage
Upload an image from the `sample_images` folder (or your own) and the app will:
- run OCR on the label
- try to find a matching product in MongoDB
- if it has a valid barcode and exists in Open Food Facts, show ingredients and nutrition

## Project Structure
- `app.py`: Streamlit app. Glues everything together (OCR + MongoDB + Open Food Facts).
- `ocr_helper.py`: OCR utilities (image preprocessing, text extraction, barcode/keyword parsing).
- `database.py`: MongoDB connection and search helpers.
- `api_helper.py`: Tiny wrapper around the Open Food Facts API (v2 product-by-barcode).
- `sample_images/`: A set of test images (Chocolates, Biscuits, Electronics) to verify the scanner.

## How the pieces work together
1. You upload an image in `app.py`.
2. `ocr_helper.extract_text` reads all the text, and we derive barcodes + product words from it.
3. The app calls `database.search_by_barcode` and `database.search_by_text` to look for a matching product in MongoDB.
4. If a barcode was found, `api_helper.fetch_food_details` asks Open Food Facts for the nutrition info for that barcode.
5. The Streamlit UI then shows:
   - what OCR read,
   - the matching MongoDB product (name/category/popularity),
   - and, only when available, ingredients + nutrition from Open Food Facts.

## Known challenges
- OCR can still fail on very shiny / curved labels or very low resolution images.
- Many products (especially non-food) are not in Open Food Facts, so nutrition will be empty in those cases.

## Possible improvements
- Better OCR tuning and more languages.
- Use even more processing and other techniques to improve OCR accuracy.
- Can use more advanced techniques to improve OCR accuracy.
- Smarter matching logic between OCR text and MongoDB entries.
- Nicer Streamlit UI with more product details and filters.
- could utilize the open food facts API to get more information about the product.


## Output Screenshots : 

![Sample Image 1](Screenshots%20of%20Working%20of%20the%20Project/sample%20image%201.png)

![Sample Image 3](Screenshots%20of%20Working%20of%20the%20Project/sample%20image%203.png)

![Sample Image 4](Screenshots%20of%20Working%20of%20the%20Project/sample%20image%204.png)

