#####################################################################################
# IMAGE TO TEXT APP
# BY CHADEE FOUAD
# SHADY555@GMAIL.COM
# NOV 2024
# 
# KEY NOTES FOR WEB DEPLOYMENT:
# EVERY EXCEPT / PASS COMMAND IS TP ALLOW THE APP TO WORK ON BOTH WINDOWS AND WEB
# CASE DOESN'T MATTER ON WINDOWS BUT IT MATTERS ON WEB. MAKE SURE FILE NAMES ARE
# HAVING A CONSISTENT CASE (PREFERABLY LOWERCASE)
# REQUIRMENTS.TXT IS A MUST FOR WEB DEPLOYMENT. CMD Command: pipreqs . --force
#####################################################################################



#####################################################################################
# To  address pytesseract not in PATH when DEPLOYING ON THE WEB:  
# https://discuss.streamlit.io/t/how-to-extract-characters-from-the-image-using-googles-tesseract-and-print-them-on-the-streamlit-application/17514/2
# The installation instructions for pytesseract say that Google’s tesseract-ocr is a dependency. Meaning, you need to install tesseract-ocr as an apt-get dependency (for Linux applications outside the Python environment).
#
# The way to do that is to include the necessary dependencies in a packages.txt file in your repo:
#
# Create a new packages.txt file with the following lines:
#
# tesseract-ocr
# tesseract-ocr-por
# The first line installs the base tesseract-ocr application and supports only English by default. To support Portuguese, you need to install a language specific tesseract data file, which we do in the second line.
#
# Reboot your app
#
# Once you make the above changes, your app should successfully deploy! :tada:
#####################################################################################




import streamlit as st
from PIL import Image, ImageEnhance
import pytesseract
import io
import zipfile
import os
import base64
import cv2
import numpy as np
#import fitz  # PyMuPDF
import pymupdf
from streamlit_pdf_viewer import pdf_viewer




# Function to process the PDF and return a list of (filename, file data) tuples
def process_pdf(file):
    pdf_document = pymupdf.open(stream=file.read(), filetype="pdf")    
    saved_files = []
    filenames = []  # List to store (filename, file_data) for each page
    num_pages = len(pdf_document)
    #st.write(f"Total pages in document: {num_pages}")
   

    # Process each page
    for page_num in range(num_pages):
        # st.write(f"Processing page {page_num + 1}...")
        try:
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(colorspace=pymupdf.csRGB, alpha=False)  # Get the entire page as an RGB pixmap with no alpha channel
            
            # Convert the pixmap to a PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Extract digits-only text from the image
            extracted_text = extract_text_from_image(img, page_num)
            

            # Create a new PDF document and insert just the single page
            new_pdf = pymupdf.open()  # Create a new PDF
            new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)  # Add the single page

            # Use in-memory bytes buffer to store PDF instead of saving to disk
            pdf_buffer = io.BytesIO()
            new_pdf.save(pdf_buffer)
            new_pdf.close()

            pdf_buffer.seek(0)  # Reset buffer to start

            # Append the filename and file data to the list
            filename = (f"{extracted_text}.pdf")
            saved_files.append((filename, pdf_buffer))
            filenames.append('Page ' + str(page_num + 1) + ': ' + filename)

        except Exception as e:
            st.error(f"Error processing page {page_num + 1}: {e}")
            continue

    return saved_files, num_pages, filenames  # Return the number of pages along with the saved files and extracted digits




def extract_text_from_image(img, page_num):
    
    def extract_raw_text_from_image(img):
        
        # Convert the PIL image to OpenCV format
        open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Convert image to HSV color space for red text detection
        hsv = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2HSV)

        # Define red color range in HSV
        lower_red = np.array([0, 120, 70])
        upper_red = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red, upper_red)

        lower_red = np.array([170, 120, 70])
        upper_red = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red, upper_red)

        # Combine masks for red color
        red_mask = mask1 | mask2

        # Find contours of the masked red areas
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Initialize a bounding box for all red text
        x_min, y_min, x_max, y_max = open_cv_image.shape[1], open_cv_image.shape[0], 0, 0

        # Loop over contours to find the extreme bounding coordinates
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            x_min, y_min = min(x_min, x), min(y_min, y)
            x_max, y_max = max(x_max, x + w), max(y_max, y + h)

        # Define padding for the box
        xpadding, ypadding = 25, 5
        x_min, y_min = max(0, x_min - xpadding), max(0, y_min - ypadding)
        x_max, y_max = min(open_cv_image.shape[1], x_max + xpadding), min(open_cv_image.shape[0], y_max + ypadding)

        # Crop to the bounding box with padding
        cropped_image = open_cv_image[y_min:y_max, x_min:x_max]
        
        # Use pytesseract to extract text from the cropped image
        extracted_text = pytesseract.image_to_string(cropped_image)
        extracted_text = extracted_text.strip()
        
        if debug:
            st.image(cropped_image, caption='')
            st.write('Raw Text: ' + extracted_text)
        
        return extracted_text, cropped_image


    def try_different_filters(cropped_image):

        # If extracted_text is empty, apply different enhancement techniques
        
        # Convert to grayscale
        grayscale_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        
        # Technique 1: Apply GaussianBlur to reduce noise
        blurred_image = cv2.GaussianBlur(grayscale_image, (5, 5), 0)
        extracted_text = pytesseract.image_to_string(blurred_image)
        
        # Technique 2: Apply adaptive thresholding for high contrast
        if not extracted_text.strip():
            threshold_image = cv2.adaptiveThreshold(
                grayscale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            extracted_text = pytesseract.image_to_string(threshold_image)
        
        # Technique 3: Sharpen the image to enhance text
        if not extracted_text.strip():
            kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
            sharpened_image = cv2.filter2D(grayscale_image, -1, kernel)
            extracted_text = pytesseract.image_to_string(sharpened_image)
        
        return extracted_text


    def fix_ocr_errors(extracted_text, page_num):

        # Common OCR digit-character misinterpretations
        corrections = {
            'O': '0',  # O -> 0
            'o': '0',  # O -> 0
            'I': '1',  # I -> 1
            'i': '1',  # I -> 1
            'l': '1',  # l -> 1
            'S': '5',  # S -> 5
            'Z': '2',  # Z -> 2
            'b': '6',  # b -> 6
            'B': '8',  # B -> 8
            'v': '0',  # B -> 8
            'y': '0',  # B -> 8
        }
        
        # Apply replacements
        for char, replacement in corrections.items():
            extracted_text = extracted_text.replace(char, replacement)

        extracted_text = ''.join([char for char in extracted_text if char.isdigit()])
        
        # Check if extracted_text is a number, if not set it to "Page X"
        failed_detection = False
        if not extracted_text.isdigit(): failed_detection = True
        if len(extracted_text) < 5: failed_detection = True
        if extracted_text[:2]!='00': extracted_text = '00' + extracted_text[-5:]
        if failed_detection: extracted_text = f"Page_{page_num + 1}"   
        return extracted_text


    ################################################################################################################
    # MAIN FLOW OF THIS SECTION
    ################################################################################################################
    extracted_text, cropped_image = extract_raw_text_from_image(img)
    if not extracted_text: extracted_text = try_different_filters(cropped_image)
    extracted_text = fix_ocr_errors(extracted_text, page_num)
    if debug: st.write('Fixed Text: ' + extracted_text)
    return extracted_text






# Function to create a zip file containing all the PDF files, including the uploaded file
def create_zip(uploaded_file, files, num_pages):
    zip_buffer = io.BytesIO()  # In-memory zip file
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        if num_pages > 1:
            uploaded_file.seek(0)
            zf.writestr(uploaded_file.name, uploaded_file.read())

        # Add each processed PDF to the zip
        for filename, file_data in files:
            zf.writestr(filename, file_data.getvalue())

    zip_buffer.seek(0)  # Reset buffer to start
    return zip_buffer

# Function to convert PDF to base64
def convert_pdf_to_base64(pdf_file):
    pdf_bytes = pdf_file.read()
    encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return encoded_pdf

# Function to set up the UI
def setup_ui():
    title = 'Scanned Image To Text (OCR) App'
    st.set_page_config(page_title=title, layout="wide", page_icon=":file_folder:")
    st.markdown('<h1 style="color: limegreen;">' + title + '</h1>', unsafe_allow_html=True)
    
    # Add background image
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://img.freepik.com/free-vector/abstract-wave-element-design-blue-curve-light-lines-background-digital-frequency-track-equalizer-generative-ai_1423-11938.jpg");
            background-attachment: fixed;
            background-size: cover
        }
        .reportview-container {
            background: rgba(0,0,0,0.5);
        }
        .sidebar .sidebar-content {
            background: rgba(0,0,0,0.5);
        }
        </style>
        """,
        unsafe_allow_html=True
    )



# Function to display the PDF
def display_pdf(base64_pdf):
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <embed src="data:application/pdf;base64,{base64_pdf}" 
            width="1000" height="1000" type="application/pdf">
        </div>
        """,
        unsafe_allow_html=True
    )

    






def show_expander():

    with st.expander('Click Here To Open The [ABOUT] Section & To  A Sample File For Trying The App!'):
        st.markdown("## About")
        st.markdown("Developer: Chadee Fouad - MyWorkDropBox@gmail.com  \nDevelopment Date: Aug 2024.")
        st.markdown("Credit for wallpaper image goes to: https://wallpapercave.com/")

        st.write("")
        text = 'Purpose:'
        text = text + "  \nThis can be used as a generic app for splitting large pdfs file into a seperate pdf for each page.\n"
        text = text + "  \n\nIn addition this app is also designed to solve a difficult problem for a friend:"
        text = text + '  \nCurrently Product Delivery Orders come as a large scanned PDF file. The follwing is required on this file: '
        text = text + "  \n1- Create a seperate file for each page."
        text = text + "  \n2- Use AI Machine vision to read the Delivery Order Number in the pdf."
        text = text + "  \n3- Rename the file to be the same as the order number in the scanned image so that it's easy to search for the Delivery Order when needed."
        text = text + "  \n4- If the AI fails to detect the Delivery Order Number, name the file with its page number for further investigation."
        text = text + "  \n5- Create a zip file which contains the original file plus all the extracted files."
        text = text + "  \n\nThis app does that, which saves an enormous time and reduces errors as opposed to doing it manually for hundreds of files.\n\n" 
        text = text + "  \n\n\n\nKey Challenges:" 
        text = text + "  \n1- Dynamically detecting the area of the Delivery Order Number within the scanned image." 
        text = text + "  \n2- Bad printing quality causing some parts of the number to be missing, which confuses AI." 
        text = text + "  \n3- Numbers being treated as text. e.g. o vs. 0 or I vs. 1." 
        text = text + "  \n4- Sometimes there's handwriting with a pen over the numbers which confuses the detection algorithm" 
        text = text + "  \n5- Different image colors." 
        text = text + "  \n\nTo Address Those Challenges:" 
        text = text + "  \n1- I've used various filters in order to find the best quality. Filters include pure black & white, greyscale, etc." 
        text = text + "  \n2- Several error detection and correction techniques to ensure that the right pattern is being captured." 

        st.markdown(text)

        with open("sample.pdf", "rb") as pdf_file:
            # ALERT!! Make file name all in small letters to avoid errors during web deployment. It gives an error when using 'Sample.pdf'
            document = pdf_file.read()

        if st.download_button(
            label=" Sample PDF File For Testing The Application!",
            key="_button",
            on_click=None,  # You can specify a callback function if needed
            file_name="sample.pdf",
            data=document,
            help="Click to download.",
        ):
            # Show success message after clicking 
            text = 'Great! Now locate the ed file and drag it to the [Drag And Drop File Here] area at the top of the page.'
            text = text + '  \nThen click on the "OUTPUT" tab to see the demo results.'
            st.success(text)





# Main app logic
def main():

    
    setup_ui()

                   
    # File uploader
    uploaded_file = st.file_uploader("Upload the consolidated PDF file containing Delivery Orders' Scanned Images to split into seperate files. Each file will be named with the Delivery Order number in the scanned image:", type="pdf")
    show_expander()
    
    if uploaded_file is not None:

        # Process the PDF and get saved files in memory
        saved_files, num_pages, filenames = process_pdf(uploaded_file)
        
        # Get the uploaded filename and change the extension to .zip
        uploaded_filename = os.path.splitext(uploaded_file.name)[0]
        zip_filename = f"{uploaded_filename}.zip"
        
        # Create a ZIP file containing the uploaded file and all the PDFs
        if saved_files:
            zip_file = create_zip(uploaded_file, saved_files, num_pages)
            
           
            
            
            # Set up the two-column layout
            col1, col2 = st.columns([7, 3])  # Ratio 70% : 30%

            # Display the PDF in the left column
            with col1:

                # NOTE: For some reason the embedding of PDF does not work when deployed on the web. However, it works nicely on Windows and it's much better than using pdf_viewer library
                # FOR PREVIEW ON WINDOWS
                if os.name == 'nt':
                    uploaded_file.seek(0)
                    base64_pdf = convert_pdf_to_base64(uploaded_file)
                    display_pdf(base64_pdf) # Works on Windows but does NOT WORK WHEN DEPLOYING ON STREAMLIT COMMUNITY
                else:
                    # Convert PDF to base64 and display it
                    binary_data = uploaded_file.getvalue() 
                    st.write('Displaying first 15 pages:')
                    #pdf_viewer(input=binary_data, width=800, pages_to_render = 1) #, rendering= 'legacy_iframe ') # FOR PREVIEW ON THE WEB
                    pdf_viewer(input=binary_data, width=800, pages_to_render=[1, 2]) # FOR PREVIEW ON THE WEB


            # Display extracted digits in the right column
            with col2:
                 # Provide a  button for the ZIP file
                
                st.write('Progress Report')
                st.write(f"Total pages in document: {num_pages}")


                st.download_button(
                    label="Download Extracted Files",
                    data=zip_file,
                    file_name=zip_filename,
                    mime="application/zip"
                )
            
                for filename in filenames: st.write(filename)
                    

        else:
            st.error("No pages were processed.")
    else:
        # Add instructions
        st.markdown(""" 
        ### Instructions:
        1. Upload a PDF file using the file uploader above.
        2. Once uploaded, the app will process the file and create a ZIP archive.
        3. The ZIP archive will contain separate PDF files for each page of the original document.     
        4. Click the ' Files' button to  the archive.
        5. The uploaded PDF will be displayed below.
        """)

debug = False
if __name__ == "__main__":
    main()
