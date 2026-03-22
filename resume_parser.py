import os
import re
import logging

try:
    import PyPDF2
except ImportError:
    logging.warning("PyPDF2 is not installed. Please install it using 'pip install PyPDF2'")

# Configure basic logging for the module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def clean_text(text: str) -> str:
    """
    Cleans the extracted text by removing extra whitespaces and newlines.
    
    Args:
        text (str): The raw text extracted from PDF.
        
    Returns:
        str: The cleaned text string.
    """
    if not text:
        return ""
        
    # Replace multiple newlines with a single space
    text = re.sub(r'[\r\n]+', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading and trailing spaces
    return text.strip()

def extract_resume_text(pdf_path: str) -> str:
    """
    Extracts and cleans all text from a given PDF resume file using PyPDF2.
    
    Args:
        pdf_path (str): The absolute or relative path to the PDF file.
        
    Returns:
        str: Cleaned text extracted from the PDF, or an empty string if it fails.
    """
    if not os.path.exists(pdf_path):
        logging.error(f"File not found: {pdf_path}")
        return ""
    
    if not pdf_path.lower().endswith('.pdf'):
        logging.error(f"Invalid file type. Expected a PDF file: {pdf_path}")
        return ""
        
    extracted_text = []
    
    try:
        with open(pdf_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
            except Exception as e:
                logging.error(f"Failed to read the PDF file (it may be corrupted or encrypted): {e}")
                return ""
            
            num_pages = len(pdf_reader.pages)
            if num_pages == 0:
                logging.warning(f"The PDF file is empty (0 pages): {pdf_path}")
                return ""
                
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                    
        full_text = " ".join(extracted_text)
        
        if not full_text.strip():
            logging.warning(f"No parseable text found in the PDF. It might be a scanned image: {pdf_path}")
            return ""
            
        cleaned_text = clean_text(full_text)
        logging.info(f"Successfully extracted {len(cleaned_text)} characters from '{os.path.basename(pdf_path)}'.")
        return cleaned_text
        
    except PermissionError:
        logging.error(f"Permission denied to read file: {pdf_path}")
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing '{pdf_path}': {e}")
        return ""


if __name__ == "__main__":
    
    print("--- Resume Parser ---")
   
    sample_pdf = input("Enter the path to a PDF resume (e.g., resume.pdf): ").strip().strip('"').strip("'")
    
    if sample_pdf:
        print("\nExtracting text...")
        resume_text = extract_resume_text(sample_pdf)
        
        if resume_text:
            print("\n--- Extracted Resume Text ---")
            print(resume_text[:500] + ("..." if len(resume_text) > 500 else ""))
            print(f"\n[Total length: {len(resume_text)} characters]")
        else:
            print("\nExtraction failed or returned empty text.")
    else:
        print("No file path provided.")
