import pymupdf
import os

# Constants
DPI = 350  # Can be modified as needed

def convert_pdf_to_images(pdf_path, output_dir, max_pages=None):
    """
    Convert PDF pages to images.
    Args:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save images.
        max_pages (int, optional): Maximum number of pages to convert. None for all pages.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_document = pymupdf.open(pdf_path)

    image_files = []
    
    total_pages = pdf_document.page_count
    pages_to_convert = min(total_pages, max_pages) if max_pages else total_pages

    for page_number in range(pages_to_convert):
        page = pdf_document[page_number]
        pix = page.get_pixmap(dpi=DPI)
        output_file = os.path.join(output_dir, f'page_{page_number + 1:02}.png')
        pix.save(output_file)
        image_files.append(output_file)

    pdf_document.close()
    return image_files
