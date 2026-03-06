#!/usr/bin/env python3
"""Re-extract letter text from state pages and extract PDF text as markdown."""

import json
import os
import re
import time

import fitz  # PyMuPDF
import pymupdf4llm
import pytesseract
import requests
from bs4 import BeautifulSoup
from PIL import Image

BASE_URL = "https://www.fns.usda.gov"
INDEX_URL = f"{BASE_URL}/snap/waivers/foodrestriction"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SNAP-Waiver-Research/1.0 (academic research)"
})

STATES = [d for d in os.listdir("states") if os.path.isdir(os.path.join("states", d))]

# Patterns that indicate garbled text from image/seal extraction
GARBLED_PATTERNS = re.compile(
    r'[·~•Jr]{3,}'       # clusters of special chars from USDA seal
    r'|[\x00-\x08]'      # control characters
    r'|[!/:;,]{4,}'      # long runs of punctuation
    r'|[a-z]{1,2}[/:·~]{2,}[a-z]{1,2}'  # letter-symbol-letter garble
    r"|[a-z]{1,3}['/,;:]{2,}[a-z]{1,3}['/,;:]{2,}"  # garbled font encoding (e.g. cNial'j,:8/'ui)
)


def page_needs_ocr(text):
    """Check if a page's extracted text is garbled and needs OCR fallback."""
    lines = text.strip().split("\n")
    if not lines:
        return False

    short_garbled = 0
    short_total = 0
    for line in lines:
        line = line.strip()
        if not line or len(line) > 80:
            continue
        short_total += 1
        alpha_chars = sum(1 for c in line if c.isalpha())
        if len(line) > 0 and alpha_chars / len(line) < 0.4:
            short_garbled += 1

    if short_total > 0 and short_garbled / short_total > 0.3:
        return True

    if GARBLED_PATTERNS.search(text[:500]):
        return True

    return False


def ocr_page(pdf_path, page_num):
    """Render a PDF page to image and OCR it with Tesseract."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    # Render at 300 DPI for good OCR quality
    mat = fitz.Matrix(300 / 72, 300 / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    text = pytesseract.image_to_string(img)
    return text.strip()


def post_process_markdown(text):
    """Clean up extracted markdown text."""
    # Remove garbled USDA seal/signature lines (non-word chars mixed with few letters)
    text = re.sub(r'\n#{0,6}\s*\S*[/\',:;·~•]{3,}\S*[^\n]*\n', '\n', text)

    # Remove "Page X of Y" footers (with or without markdown bold formatting)
    text = re.sub(r'\n*Page\s+\*{0,2}\d+\s+of\s+\d+\*{0,2}\s*\n*', '\n', text)

    # Remove isolated bullet markers (• on a line by itself, with or without markdown header prefix)
    text = re.sub(r'\n\s*#{0,6}\s*[•·]\s*\n', '\n', text)

    # Remove empty markdown headers (### on a line by itself)
    text = re.sub(r'\n\s*#{1,6}\s*\n', '\n', text)

    # Remove lines that are just dashes/underscores (decorative separators from PDF)
    text = re.sub(r'\n\s*[-_]{10,}\s*\n', '\n', text)

    # Collapse 3+ blank lines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_pdf_markdown(pdf_path):
    """Extract markdown from a PDF using pymupdf4llm with OCR fallback."""
    try:
        # Get per-page markdown chunks
        pages = pymupdf4llm.to_markdown(
            pdf_path,
            page_chunks=True,
            write_images=False,
        )

        result_parts = []
        for i, page_data in enumerate(pages):
            page_text = page_data["text"] if isinstance(page_data, dict) else str(page_data)

            if page_needs_ocr(page_text):
                print(f"    Page {i + 1}: OCR fallback (garbled text detected)")
                try:
                    page_text = ocr_page(pdf_path, i)
                except Exception as e:
                    print(f"    OCR failed for page {i + 1}: {e}")
                    # Keep original text as fallback

            result_parts.append(page_text)

        combined = "\n\n".join(result_parts)
        return post_process_markdown(combined)

    except Exception as e:
        print(f"  ERROR extracting markdown from {pdf_path}: {e}")
        return None


def fetch_page(url):
    time.sleep(1)
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def html_to_text(element):
    """Convert HTML element to clean text, preserving paragraph breaks."""
    for br in element.find_all("br"):
        br.replace_with("\n")
    for p in element.find_all("p"):
        p.insert_before("\n\n")
        p.insert_after("\n\n")
    for li in element.find_all("li"):
        li.insert_before("\n- ")
    for h in element.find_all(re.compile(r'^h[1-6]$')):
        level = int(h.name[1])
        h.insert_before(f"\n\n{'#' * level} ")
        h.insert_after("\n\n")

    text = element.get_text()
    lines = text.split("\n")
    lines = [line.strip() for line in lines]
    result = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 2:
                result.append("")
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result).strip()


def extract_letter_from_page(slug):
    """Re-fetch and extract the letter text properly."""
    url = f"{INDEX_URL}/{slug}"
    print(f"  Fetching {url}...")
    soup = fetch_page(url)

    body = soup.find("div", class_="field--name-field-body")
    if not body:
        body = soup.find("div", class_="field--name-body")
    if not body:
        body = soup.find("div", class_="wysiwyg-container")

    if body:
        return html_to_text(body)
    return None


def process_state(slug):
    """Process a single state: re-extract letter and extract PDF markdown."""
    state_dir = os.path.join("states", slug)
    meta_path = os.path.join(state_dir, "metadata.json")

    with open(meta_path) as f:
        metadata = json.load(f)

    state_name = metadata["state"]
    print(f"\nProcessing {state_name}...")

    # Re-extract letter text
    letter_text = extract_letter_from_page(slug)
    if letter_text:
        letter_path = os.path.join(state_dir, "letter.md")
        with open(letter_path, "w") as f:
            f.write(f"# {metadata.get('title', state_name)}\n\n")
            f.write(f"**Source:** {metadata['page_url']}\n\n")
            f.write("---\n\n")
            f.write(letter_text)
            f.write("\n")
        print(f"  Updated letter.md")

    # Extract markdown from PDFs
    for enc in metadata.get("enclosures", []):
        filename = enc.get("filename")
        if not filename or not filename.endswith(".pdf"):
            continue
        pdf_path = os.path.join(state_dir, filename)
        if not os.path.exists(pdf_path):
            continue

        md_filename = filename.replace(".pdf", ".md")
        md_path = os.path.join(state_dir, md_filename)

        text = extract_pdf_markdown(pdf_path)
        if text:
            with open(md_path, "w") as f:
                f.write(f"# {filename}\n\n")
                f.write(f"**Source:** {enc.get('source_url', 'N/A')}\n\n")
                f.write("---\n\n")
                f.write(text)
                f.write("\n")
            print(f"  Extracted: {md_filename} ({len(text)} chars)")

        # Remove old .txt file if it exists
        old_txt = os.path.join(state_dir, filename.replace(".pdf", ".txt"))
        if os.path.exists(old_txt):
            os.remove(old_txt)
            print(f"  Removed old: {filename.replace('.pdf', '.txt')}")


def main():
    for slug in sorted(STATES):
        process_state(slug)
    print("\nDone!")


if __name__ == "__main__":
    main()
