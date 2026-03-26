"""
OCR Cleanup Script for Fatawa Text Files

Scans all text files in data/text/, applies rule-based corrections,
writes cleaned files to data/text_clean/, and logs all changes to
data/ocr_corrections.csv (Google Sheets compatible).
"""

import os
import re
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEXT_DIR = BASE_DIR / "data" / "text"
CLEAN_DIR = BASE_DIR / "data" / "text_clean"
CORRECTIONS_CSV = BASE_DIR / "data" / "ocr_corrections.csv"
WORD_CORRECTIONS_CSV = BASE_DIR / "scripts" / "config" / "word_corrections.csv"

# ---------------------------------------------------------------------------
# Rule 1: Noise lines to remove entirely
# ---------------------------------------------------------------------------
NOISE_PATTERNS = [
    re.compile(r"^Portal of the.*Presidency\s*$", re.IGNORECASE),
    re.compile(r"^.*Schola[ft]ly.*Research and Ifta", re.IGNORECASE),
    re.compile(r"^[.\s]*of Scholarly.*Research and Ifta", re.IGNORECASE),
    re.compile(r"^The General Presidency of Scholarly Research and Ifta.*All Rights Reserved\.\s*$"),
    re.compile(r"^Udi\s*-\s*$"),
    re.compile(r"^~\s*[a-z]?\s*$"),
    re.compile(r"^5\s*[''].* ;\s*i\s*$"),
    re.compile(r"^——\s*\d+\s*$"),
    re.compile(r"^(iG|@@)\s*Print this page.*$"),
    re.compile(r"^a eagle Fatwa-Online\.com\s*$"),
    re.compile(r"^SCHOLARS BIOGRAPHIES.*$"),
]

# ---------------------------------------------------------------------------
# Rule 2: Arabic salutation — corrupted "(peace be upon him)" honorific
# ---------------------------------------------------------------------------
# The OCR mangles the Arabic script for "salla Allahu alayhi wa sallam"
# into patterns like: plug ate alll sLe, plisg dulce all Lo, etc.
SALUTATION_PATTERN = re.compile(
    r"(plug|plus|plu\s*9|plisg|pling|plw9|ploog|plu)"
    r"\s+"
    r"(ate|atc|ale|alc|ade|adc|ace|ule|ayle|aule|arte|asle|ole|dulce|auc)"
    r"\s+"
    r"alll?\s*"
    r"[._]?\s*"
    r"[a-zA-Z¢€¥]*[Ll]*[oe]?\s*[)}>\]]?\s*[.,]?"
    r"(?:\s*[a-zA-Z]*[Ll][oe])?",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Rule 3: Symbol corrections
# ---------------------------------------------------------------------------
def apply_symbol_fixes(line):
    """Fix OCR symbol corruptions: ¢→(, €→(, ¥→V, etc."""
    corrections = []

    # ¥ followed by uppercase letter → V + letter (e.g. ¥irtue → Virtue)
    new = re.sub(r"¥([A-Z])", r"V\1", line)
    if new != line:
        corrections.append(("symbol_fix", line.strip(), new.strip()))
        line = new

    # ¥ followed by lowercase → remove stray ¥ (e.g. ¥Wudu → Wudu)
    new = re.sub(r"¥([a-z])", r"\1", line)
    if new != line:
        corrections.append(("symbol_fix", line.strip(), new.strip()))
        line = new

    # ¢ used as opening parenthesis
    new = re.sub(r"¢", "(", line)
    if new != line:
        corrections.append(("verse_bracket", line.strip(), new.strip()))
        line = new

    # € used as opening parenthesis
    new = re.sub(r"€", "(", line)
    if new != line:
        corrections.append(("verse_bracket", line.strip(), new.strip()))
        line = new

    # £ used as stray character
    new = re.sub(r"£", "", line)
    if new != line:
        corrections.append(("symbol_fix", line.strip(), new.strip()))
        line = new

    return line, corrections

# ---------------------------------------------------------------------------
# Rule 4: Word corrections from CSV dictionary
# ---------------------------------------------------------------------------
def load_word_corrections(csv_path):
    """Load word correction rules from CSV file."""
    rules = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row["original"].strip()
            corrected = row["corrected"].strip()
            context = row.get("context_pattern", "").strip()
            if context:
                pattern = re.compile(context)
            else:
                # Default: match the word with word boundaries
                pattern = re.compile(re.escape(original))
            rules.append((original, corrected, pattern))
    return rules


def apply_word_corrections(line, word_rules):
    """Apply dictionary-based word corrections to a line."""
    corrections = []
    for original, corrected, pattern in word_rules:
        if pattern.search(line):
            new_line = pattern.sub(corrected, line)
            if new_line != line:
                corrections.append(("word_correction", line.strip(), new_line.strip()))
                line = new_line
    return line, corrections

# ---------------------------------------------------------------------------
# Rule 5: Question marker normalization
# ---------------------------------------------------------------------------
QUESTION_MARKER_FIXES = [
    (re.compile(r"^QO:"), "Q:"),
    (re.compile(r"^0\s*(\d):"), r"Q\1:"),
]


def apply_question_fixes(line):
    corrections = []
    for pattern, replacement in QUESTION_MARKER_FIXES:
        new = pattern.sub(replacement, line)
        if new != line:
            corrections.append(("question_marker", line.strip(), new.strip()))
            line = new
    return line, corrections

# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def clean_line(line, word_rules):
    """Apply all correction rules to a single line. Returns (cleaned_line, corrections_list)."""
    all_corrections = []
    stripped = line.strip()

    # Rule 1: Check if entire line is noise
    for pattern in NOISE_PATTERNS:
        if pattern.match(stripped):
            return None, [("noise_line", stripped, "[REMOVED]")]

    # Rule 2: Arabic salutation
    if SALUTATION_PATTERN.search(line):
        new_line = SALUTATION_PATTERN.sub("(peace be upon him)", line)
        if new_line != line:
            all_corrections.append(("arabic_salutation", line.strip(), new_line.strip()))
            line = new_line

    # Rule 3: Symbol fixes
    line, corrs = apply_symbol_fixes(line)
    all_corrections.extend(corrs)

    # Rule 4: Word corrections
    line, corrs = apply_word_corrections(line, word_rules)
    all_corrections.extend(corrs)

    # Rule 5: Question markers
    line, corrs = apply_question_fixes(line)
    all_corrections.extend(corrs)

    return line, all_corrections


def clean_file(input_path, output_path, word_rules):
    """Process a single text file. Returns list of (file, line_no, original, corrected, error_type)."""
    corrections = []
    cleaned_lines = []
    filename = os.path.basename(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            cleaned, line_corrections = clean_line(line, word_rules)

            for error_type, original, corrected in line_corrections:
                corrections.append({
                    "file": filename,
                    "line_number": line_no,
                    "original_text": original[:200],  # truncate for CSV readability
                    "corrected_text": corrected[:200],
                    "error_type": error_type,
                })

            if cleaned is not None:
                cleaned_lines.append(cleaned)

    # Write cleaned output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    return corrections


def main():
    print(f"Loading word corrections from {WORD_CORRECTIONS_CSV}")
    word_rules = load_word_corrections(WORD_CORRECTIONS_CSV)
    print(f"  Loaded {len(word_rules)} word correction rules")

    all_corrections = []
    txt_files = sorted(TEXT_DIR.glob("*.txt"))
    print(f"\nProcessing {len(txt_files)} text files...")

    for txt_file in txt_files:
        output_path = CLEAN_DIR / txt_file.name
        corrections = clean_file(txt_file, output_path, word_rules)
        all_corrections.extend(corrections)
        n = len(corrections)
        if n > 0:
            print(f"  {txt_file.name}: {n} corrections")

    # Write corrections CSV
    print(f"\nWriting {len(all_corrections)} corrections to {CORRECTIONS_CSV}")
    with open(CORRECTIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "line_number", "original_text", "corrected_text", "error_type"])
        writer.writeheader()
        writer.writerows(all_corrections)

    # Summary
    from collections import Counter
    type_counts = Counter(c["error_type"] for c in all_corrections)
    print("\n--- Correction Summary ---")
    for error_type, count in type_counts.most_common():
        print(f"  {error_type}: {count}")
    print(f"  TOTAL: {len(all_corrections)}")
    print(f"\nCleaned files written to: {CLEAN_DIR}")
    print(f"Corrections log written to: {CORRECTIONS_CSV}")


if __name__ == "__main__":
    main()
