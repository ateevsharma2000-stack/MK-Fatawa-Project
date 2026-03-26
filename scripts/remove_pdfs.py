import os

pdf_dir = 'data/pdf'
text_dir = 'data/text'

# Get list of text files without extension
text_files = {os.path.splitext(f)[0] for f in os.listdir(text_dir) if f.endswith('.txt')}

# Iterate over PDF files and remove if corresponding text file exists
for pdf_file in os.listdir(pdf_dir):
    if pdf_file.endswith('.pdf'):
        pdf_name = os.path.splitext(pdf_file)[0]
        if pdf_name in text_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            os.remove(pdf_path)
            print(f'Removed: {pdf_path}')
