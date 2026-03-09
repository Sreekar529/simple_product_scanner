# importing necessary libraries
import re
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import ocr_helper
import database
import api_helper

# using app.py file to define streamlit interface and how it gets the  info and details from other  helper modules and displays the information required to show in the final output
st.set_page_config(page_title="Product Scanner Pro", layout="wide")

@st.cache_resource
def load_ocr():
    # Make the OCR reader once and reuse it between runs
    return ocr_helper.initialize_ocr()

@st.cache_resource
def load_database():
    # COnnects once to MongoDB and reuses the collection
    return database.connect_to_database()

def main():
    st.title(" Product Information Scanner") # title of the app
    st.markdown("Designed for rapid product identification using OCR and MongoDB Trend Analysis.")
    st.markdown("---")
    
    # Get OCR + DB ready
    ocr_reader = load_ocr()
    db_collection = load_database()
    
    # If DB is down, no point going further
    if db_collection is None:
        st.error(" Database connection failed. Please check your internet and MongoDB credentials.")
        return

    st.sidebar.info(" **Tips for best results:**\n- Ensure good lighting\n- Keep the product label centered\n- Clear images of barcodes are highly effective")
    
    uploaded_file = st.file_uploader("Upload Product Label or Image", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1.2])
        image = Image.open(uploaded_file)
        
        with col1:
            st.subheader(" Original Image")
            st.image(image, use_column_width=True)
            
            # Optional: show how the cleaned image looks to OCR
            if st.checkbox("Show OCR Preprocessed Image"):
                image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                processed = ocr_helper.preprocess_image(image_cv)
                st.image(processed, caption="What the AI 'sees'", use_column_width=True)
            
        with col2:
            st.subheader(" Analysis Results")
            
            # Convert PIL image into OpenCV format
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            with st.spinner("Analyzing image..."):
                # 1) run OCR and grab text + confidence 
                # using ocr_helper , previously defined, to extract text and confidence from the image
                text, conf = ocr_helper.extract_text(ocr_reader, image_cv)
                barcodes = ocr_helper.extract_numbers(text)
                keywords = ocr_helper.find_important_words(text)
                
                # Let user see what OCR actually read and display the text, confidence, and parsed helpers
                with st.expander(" View Raw Extracted Text"):
                    st.write(f" **Confidence:** {conf*100:.1f}%")
                    st.text(text)
                    st.write("**Detected barcodes:**", barcodes)
                    st.write("**Detected keywords:**", keywords)
                
                # First try barcode match, then fall back to text search
                results_found = False
                mongo_results = []
                search_term = ""
                
                # 1) barcode-based search in MongoDB
                if barcodes:
                    for bc in barcodes:
                        st.info(f" Scanning detected barcode: **{bc}**")
                        # using database.py file to search for the barcode in the database
                        mongo_results = database.search_by_barcode(db_collection, bc)
                        if mongo_results:
                            search_term = bc
                            results_found = True
                            break
                
                #  text-based search in MongoDB if barcode didn't help
                if not results_found and keywords:
                    #  Try the "full phrase" first for better precision using the keywords extracted from the image
                    full_phrase = " ".join(keywords)
                    st.info(f" Attempting complete search: **{full_phrase}**")
                    mongo_results = database.search_by_text(db_collection, full_phrase)
                    
                    if mongo_results:
                        search_term = full_phrase
                        results_found = True
                    else:
                        #  Fallback: Search individual keywords if full phrase fails using the keywords extracted from the image
                        #  Also add smartphone-specific inferred terms like "vivo v29" from tokens such as "v29"
                        search_candidates = list(keywords)
                        for kw in keywords:
                            # If we see something like "V29", "v29", or "V29Pro", also try "vivo v29"
                            m = re.match(r"^[Vv](\d{2})", kw)
                            if m:
                                model_digits = m.group(1)
                                inferred = f"vivo v{model_digits}"
                                if inferred not in search_candidates:
                                    search_candidates.append(inferred)

                        for kw in search_candidates:
                            st.info(f" Searching by keyword: **{kw}**")
                            mongo_results = database.search_by_text(db_collection, kw)
                            if mongo_results:
                                search_term = kw
                                results_found = True
                                break
                
                #  ask Open Food Facts using the first barcode (if we have one)
                api_data = None
                # We only query OFF if we see a barcode (no free-text search here)
                if barcodes:
                    # using api_helper.py file to fetch the food details from the open food facts API
                    api_data = api_helper.fetch_food_details(barcodes[0])
                
                # Show a match if DB worked or OFF worked
                if results_found or api_data:
                    st.success(" Match Found!")
                    
                    # Decide what name to show on top
                    if mongo_results:
                        p_name = mongo_results[0].get('product_name', search_term).title()
                    elif api_data and api_data.get('name'):
                        p_name = api_data['name'].title()
                    elif search_term:
                        p_name = search_term.title()
                    else:
                        p_name = "Unknown Product"
                    
                    st.header(f"{p_name}")
                    
                    # Show some basic info on the product
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        brand = api_data.get('brand', 'N/A') if api_data else "N/A" # using api_helper.py file to fetch the brand from the open food facts API
                        st.markdown(f" ** Brand:** {brand}")
                        
                        cat = mongo_results[0].get('category', 'N/A') if mongo_results else "N/A"
                        st.markdown(f" ** Category:** {cat}")
                    
                    with res_col2:
                        pop = mongo_results[0].get('relative_count', 'N/A') if mongo_results else "N/A"
                        st.markdown(f" ** Popularity Score:** {pop}")

                    # Only show nutrition stuff if OFF found a food product
                    st.markdown("---")
                    tab1, tab2 = st.tabs([" Ingredients", " Nutrition Facts"])
                    
                    with tab1:
                        if api_data:
                            st.write(api_data.get('ingredients', 'Information not available.'))
                        else:
                            st.warning("Ingredient data not available.")
                    
                    with tab2:
                        if api_data and api_data.get('nutrition'):
                            st.json(api_data['nutrition'])
                        else:
                            st.info("Nutrition breakdown not found.")
                else:
                    st.warning("No matches found in database or Food API. Try a clearer image or manual entry.")

if __name__ == "__main__":
    main()