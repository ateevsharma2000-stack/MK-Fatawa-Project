import os
import PyPDF2
from pdf2image import convert_from_path
import pytesseract

PDF_DIR = "data/pdf"
TEXT_DIR = "data/text"

def convert_all_pdfs_to_txt(pdf_dir=PDF_DIR, txt_dir=TEXT_DIR):
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            txt_output = os.path.join(txt_dir, filename.replace(".pdf", ".txt"))

            # Extract PDF text
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                all_text = []
                for page in reader.pages:
                    all_text.append(page.extract_text())

                    #if the page is not extractable, use pdf2image and pytesseract
                    if len(page.extract_text()) < 10:
                        all_text = []
                        pages = convert_from_path(pdf_path, dpi=300)
                        for i, page_2 in enumerate(pages):
                            # Save page temporarily if needed
                            temp_filename = f"page_{i}.png"
                            page_2.save(temp_filename, "PNG")
                            
                            # OCR the page image
                            text = pytesseract.image_to_string(page_2, lang="eng")
                            all_text.append(text)
                            
                            # Optionally remove temp image
                            os.remove(temp_filename)
                        break
                # Write out
                with open(txt_output, "w", encoding="utf-8") as out_file:
                    out_file.write("\n".join(all_text))
                print(f"Converted {filename} -> {txt_output}")

if __name__ == "__main__":
    convert_all_pdfs_to_txt()