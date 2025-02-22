import json
import re
from datetime import datetime

def parse_to_json(text: str) -> str:
    """
    Parse the raw text of Majmoo’al-Fatawa (volume 1) into a structured JSON string.

    This function looks for known headings (e.g., 'Foreword', 'Second EditionIntroduction', etc.)
    and page markers (e.g., '( Part No : 1, Page No: 5 )') to chunk the text into sections
    and sub-sections. Each section maintains a list of pages, where each page has its corresponding text.

    Args:
        text (str): The raw text to parse.

    Returns:
        str: A JSON-formatted string representing the parsed fatawa text with metadata.
    """

    # ------------------
    # 1) Basic Metadata
    # ------------------
    metadata = {
        "title": "Majmoo’al-Fatawa of late Scholar Ibn Bazz (R)",
        "edition": "Second Edition",
        "author": "Sheikh `Abdul `Aziz Bin `Abdullah ibn `AbdulRahman ibn Bazz",
        "roles": [
            "Mufti of Kingdom of Saudi Arabia",
            "Chairman of the Council of Senior Scholars",
            "Chairman of Department of Scholarly Research and Ifta'"
        ],
        "source": "http://www.alifta.com",
        "volume": "No.01 of 30",
        "timestamp": datetime.now().isoformat()
    }

    # -------------------------
    # 2) Pre-compile Regex
    # -------------------------
    heading_patterns = [
        r"Foreword",
        r"Second EditionIntroduction",
        r"Ibn Baz:\s*Concise Biography",
        r"Sound `Aqidah $begin:math:text$Creed$end:math:text$ and its contrast"
    ]
    heading_regex = re.compile("|".join(heading_patterns))

    # Matches strings like "( Part No : 1, Page No: 5 )"
    page_marker_regex = re.compile(r"$begin:math:text$\\s*Part\\s+No\\s*:\\s*\\d+\\s*,\\s*Page\\s+No\\s*:\\s*\\d+\\s*$end:math:text$")

    # ------------------------------
    # 3) Extract Sections from Text
    # ------------------------------
    sections = extract_sections(
        text=text,
        heading_regex=heading_regex,
        page_marker_regex=page_marker_regex
    )

    # ----------------------------
    # 4) Build the Final Structure
    # ----------------------------
    data = {
        "metadata": metadata,
        "sections": sections
    }

    # Convert to JSON with nice indentation
    return json.dumps(data, indent=2, ensure_ascii=False)

def extract_sections(text: str, heading_regex: re.Pattern, page_marker_regex: re.Pattern) -> list:
    """
    Splits the text into sections based on recognized headings, and page markers.
    Returns a list of sections, where each section is a dict with:
      - title: the heading text
      - pages: list of { "page": marker, "text": text_in_that_range }
    
    Args:
        text (str): Full raw text.
        heading_regex (re.Pattern): Pre-compiled regex that matches known headings.
        page_marker_regex (re.Pattern): Pre-compiled regex for page markers.

    Returns:
        list: A list of section dicts.
    """
    lines = text.strip().splitlines()

    # Prepare a default section in case we don't find headings right away
    sections = []
    current_section = {
        "title": "Miscellaneous",  # Fallback if no heading found
        "content": [],
        "pages": []
    }

    for line in lines:
        line_stripped = line.strip()

        # 1) Check if the line is a recognized heading
        if heading_regex.search(line_stripped):
            # If we already have a named section in progress, append it
            if current_section["title"] or current_section["content"]:
                # Store remaining content in the last pages block
                if current_section["content"]:
                    current_section["pages"].append({
                        "page": "EndOfSection",
                        "text": "\n".join(current_section["content"])
                    })
                sections.append(current_section)
            
            # Start a fresh section
            current_section = {
                "title": line_stripped,
                "content": [],
                "pages": []
            }

        # 2) Check if line is a page marker
        elif page_marker_regex.match(line_stripped):
            page_marker = line_stripped
            
            # If there's existing content, store it as the 'previous page' block
            if current_section["content"]:
                current_section["pages"].append({
                    "page": page_marker,
                    "text": "\n".join(current_section["content"])
                })
                # Reset content buffer for the next page
                current_section["content"] = []
            else:
                # If there's no content yet, just record that a page marker was found
                # This might happen if consecutive page markers appear
                current_section["pages"].append({
                    "page": page_marker,
                    "text": ""
                })

        # 3) Otherwise, treat it as content
        else:
            # Add non-empty lines to the current section's content
            if line_stripped:
                current_section["content"].append(line_stripped)

    # After the loop, finalize the last section if there's content
    if current_section["title"] or current_section["content"]:
        if current_section["content"]:
            current_section["pages"].append({
                "page": "EndOfSection",
                "text": "\n".join(current_section["content"])
            })
        sections.append(current_section)

    return sections

# Example of how to run if you had this in a script
if __name__ == "__main__":
    sample_text = """
( Part No : 1, Page No: 1)
Foreword
All praise is due to Allah...
( Part No : 1, Page No: 2)
This is more content on page two.
Second EditionIntroduction
Some more lines here...
( Part No : 1, Page No: 3)
Ibn Baz: Concise Biography
( Part No : 1, Page No: 4)
Sound `Aqidah (Creed) and its contrast
Example content...
"""
    json_output = parse_to_json(sample_text)
    print(json_output)