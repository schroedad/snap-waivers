#!/usr/bin/env python3
"""Re-extract letter text from state pages and extract PDF text."""

import json
import os
import re
import time

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.fns.usda.gov"
INDEX_URL = f"{BASE_URL}/snap/waivers/foodrestriction"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SNAP-Waiver-Research/1.0 (academic research)"
})

STATES = [d for d in os.listdir("states") if os.path.isdir(os.path.join("states", d))]


def fetch_page(url):
    time.sleep(1)
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def html_to_text(element):
    """Convert HTML element to clean text, preserving paragraph breaks."""
    # Replace <br> with newlines
    for br in element.find_all("br"):
        br.replace_with("\n")
    # Replace <p> boundaries with double newlines
    for p in element.find_all("p"):
        p.insert_before("\n\n")
        p.insert_after("\n\n")
    # Replace <li> with bullet points
    for li in element.find_all("li"):
        li.insert_before("\n- ")
    # Replace <h2> etc with markdown headers
    for h in element.find_all(re.compile(r'^h[1-6]$')):
        level = int(h.name[1])
        h.insert_before(f"\n\n{'#' * level} ")
        h.insert_after("\n\n")

    text = element.get_text()
    # Clean up excessive whitespace while preserving paragraph breaks
    lines = text.split("\n")
    lines = [line.strip() for line in lines]
    # Collapse multiple blank lines into two
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

    # Find the body field
    body = soup.find("div", class_="field--name-field-body")
    if not body:
        body = soup.find("div", class_="field--name-body")
    if not body:
        # Try the wysiwyg container
        body = soup.find("div", class_="wysiwyg-container")

    if body:
        return html_to_text(body)
    return None


def extract_pdf_text(pdf_path):
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                pages.append(f"--- Page {page_num + 1} ---\n\n{text.strip()}")
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  ERROR extracting text from {pdf_path}: {e}")
        return None


def process_state(slug):
    """Process a single state: re-extract letter and extract PDF text."""
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

    # Extract text from PDFs
    for enc in metadata.get("enclosures", []):
        filename = enc.get("filename")
        if not filename or not filename.endswith(".pdf"):
            continue
        pdf_path = os.path.join(state_dir, filename)
        if not os.path.exists(pdf_path):
            continue

        txt_filename = filename.replace(".pdf", ".txt")
        txt_path = os.path.join(state_dir, txt_filename)

        text = extract_pdf_text(pdf_path)
        if text:
            with open(txt_path, "w") as f:
                f.write(f"# Text extracted from: {filename}\n")
                f.write(f"# Source: {enc.get('source_url', 'N/A')}\n\n")
                f.write(text)
                f.write("\n")
            print(f"  Extracted text: {txt_filename} ({len(text)} chars)")


def main():
    for slug in sorted(STATES):
        process_state(slug)
    print("\nDone!")


if __name__ == "__main__":
    main()
