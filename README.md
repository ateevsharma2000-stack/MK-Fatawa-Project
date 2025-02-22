# Majmoo' al-Fatawa Text-to-JSON Project

This repository provides a workflow for handling PDFs of Majmoo' al-Fatawa of late Scholar Ibn Baz (R), converting them to text, and then parsing that text into structured JSON. It includes scripts for:

1. **Downloading PDFs** (if needed)  
2. **Extracting text** from PDFs  
3. **Parsing** the resulting text into JSON format

---

## Table of Contents

- [Project Overview](#project-overview)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Download PDFs (Optional)](#1-download-pdfs-optional)
  - [2. Convert PDFs to Text](#2-convert-pdfs-to-text)
  - [3. Parse Text into JSON](#3-parse-text-into-json)
- [Configuration](#configuration)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

We aim to automate the process of:

- **Collecting** all volumes of the Majmoo' al-Fatawa in PDF form  
- **Extracting** the text from each PDF  
- **Transforming** that text into a standardized JSON structure (with metadata, sections, page markers, etc.)

By following this approach, we can more easily search, analyze, or display the fatawa in web applications, data pipelines, or other platforms.

---

## Folder Structure

Below is an example layout:

```
MKFTWA_PROJ/
├── data/
│   ├── pdf/          # All original PDFs
│   ├── text/         # Extracted `.txt` files
│   ├── json/         # Output `.json` files
├── scripts/
│   ├── pdf_download.py  # Optional script to scrape/download PDFs
│   ├── pdf_to_txt.py    # Converts PDFs in `data/pdf` → text in `data/text`
│   ├── txt_to_json.py   # Parses text in `data/text` → JSON in `data/json`
│   └── config/
│       └── pdf_urls.txt # Optional: holds PDF URLs for `pdf_download.py`
├── tests/
│   ├── test_pdf_to_txt.py  # Unit tests for pdf_to_txt functionality
│   └── test_txt_to_json.py # Unit tests for txt_to_json functionality
├── .gitignore
├── README.md
├── requirements.txt
└── LICENSE (optional)
```

---

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/YourUsername/MKFTWA_PROJ.git
    cd MKFTWA_PROJ
    ```

2. **Set up a Python virtual environment (recommended)**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install the required dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

### 1. Download PDFs (Optional)

If you have a file named `pdf_urls.txt` in `scripts/config/` with links to the PDFs, you can run:

```bash
python scripts/pdf_download.py
```

This will read URLs from `scripts/config/pdf_urls.txt`, download each PDF, and place them in `data/pdf/`.

Note: If you already have the PDFs, simply place them into `data/pdf/` manually and skip this step.

### 2. Convert PDFs to Text

Run the following command to process every `.pdf` in `data/pdf/` and output `.txt` files in `data/text/`:

```bash
python scripts/pdf_to_txt.py
```

- This script iterates over all `.pdf` files in `data/pdf/`, extracts text (using a library like PyPDF2), and saves each file’s content as `.txt` in `data/text/`.

### 3. Parse Text into JSON

Convert the extracted `.txt` files into JSON by running:

```bash
python scripts/txt_to_json.py
```

- This script reads all `.txt` files in `data/text/`, parses them (detecting headings, page markers, etc.), and writes out structured JSON files to `data/json/`.

---

## Testing

If you have test scripts, place them under the `tests/` directory. For example, to run tests with pytest:

```bash
pytest tests/
```

Examples of test files might be:
- `test_pdf_to_txt.py`: Tests the PDF → text extraction.
- `test_txt_to_json.py`: Tests the text → JSON parsing logic.

---

## Contributing

1. Fork this repository.
2. Create a new branch for your feature or bug fix.
3. Make and commit your changes with descriptive messages.
4. Push to your fork/branch.
5. Open a pull request back into main.

We welcome feedback, bug reports, and improvements!

---

## License

This project is licensed under the MIT License.

