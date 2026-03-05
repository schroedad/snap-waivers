#!/usr/bin/env python3
"""Scrape SNAP food restriction waiver data from USDA FNS website."""

import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.fns.usda.gov"
INDEX_URL = f"{BASE_URL}/snap/waivers/foodrestriction"

STATES = {
    "arkansas": "Arkansas",
    "colorado": "Colorado",
    "florida": "Florida",
    "hawaii": "Hawaii",
    "idaho": "Idaho",
    "indiana": "Indiana",
    "iowa": "Iowa",
    "kansas": "Kansas",
    "louisiana": "Louisiana",
    "missouri": "Missouri",
    "nebraska": "Nebraska",
    "nevada": "Nevada",
    "northdakota": "North Dakota",
    "ohio": "Ohio",
    "oklahoma": "Oklahoma",
    "southcarolina": "South Carolina",
    "tennessee": "Tennessee",
    "texas": "Texas",
    "utah": "Utah",
    "virginia": "Virginia",
    "westvirginia": "West Virginia",
    "wyoming": "Wyoming",
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SNAP-Waiver-Research/1.0 (academic research)"
})


def fetch_page(url):
    """Fetch and parse a page, with polite delay."""
    time.sleep(1)
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def download_pdf(url, dest_path):
    """Download a PDF file."""
    if os.path.exists(dest_path):
        print(f"  Already downloaded: {dest_path}")
        return
    time.sleep(1)
    resp = SESSION.get(url, timeout=60)
    resp.raise_for_status()
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    print(f"  Downloaded: {dest_path} ({len(resp.content)} bytes)")


def scrape_index():
    """Scrape the main index page for the summary table."""
    print("Scraping index page...")
    soup = fetch_page(INDEX_URL)

    # Extract table data
    table = soup.find("table")
    if not table:
        print("WARNING: No table found on index page")
        return {}

    rows = table.find_all("tr")
    summaries = {}
    for row in rows[1:]:  # skip header
        cells = row.find_all(["td", "th"])
        if len(cells) >= 3:
            state_name = cells[0].get_text(strip=True)
            impl_date = cells[1].get_text(strip=True)
            summary = cells[2].get_text(strip=True)
            summaries[state_name] = {
                "target_implementation_date": impl_date,
                "summary_of_request": summary,
            }
    return summaries


def extract_letter_text(soup):
    """Extract the letter text from a state page."""
    # The main content area
    content = soup.find("article") or soup.find("main") or soup.find("div", class_="field--name-body")

    if not content:
        # Fallback: get the whole page text
        content = soup

    # Try to find the body field specifically
    body = soup.find("div", class_="field--name-body")
    if body:
        return body.get_text(separator="\n", strip=False).strip()

    # Try article
    article = soup.find("article")
    if article:
        return article.get_text(separator="\n", strip=False).strip()

    return content.get_text(separator="\n", strip=False).strip()


def extract_enclosures(soup):
    """Extract enclosure links (PDFs) from a state page."""
    enclosures = []
    # Look for PDF links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        if href.endswith(".pdf") or ".pdf#" in href:
            full_url = href if href.startswith("http") else BASE_URL + href
            # Strip fragment for download
            download_url = full_url.split("#")[0]
            enclosures.append({
                "title": text,
                "url": full_url,
                "download_url": download_url,
            })
    # Deduplicate by download_url
    seen = set()
    unique = []
    for e in enclosures:
        if e["download_url"] not in seen:
            seen.add(e["download_url"])
            unique.append(e)
    return unique


def scrape_state(slug, state_name, index_summaries):
    """Scrape a single state's page and download PDFs."""
    url = f"{INDEX_URL}/{slug}"
    print(f"\nScraping {state_name} ({url})...")

    state_dir = os.path.join("states", slug)
    os.makedirs(state_dir, exist_ok=True)

    soup = fetch_page(url)

    # Extract page title
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else state_name

    # Extract letter text
    letter_text = extract_letter_text(soup)

    # Extract enclosures
    enclosures = extract_enclosures(soup)

    # Download PDFs
    pdf_files = []
    for enc in enclosures:
        filename = enc["download_url"].split("/")[-1]
        dest = os.path.join(state_dir, filename)
        try:
            download_pdf(enc["download_url"], dest)
            pdf_files.append({
                "title": enc["title"],
                "filename": filename,
                "source_url": enc["url"],
            })
        except Exception as e:
            print(f"  ERROR downloading {enc['download_url']}: {e}")
            pdf_files.append({
                "title": enc["title"],
                "filename": None,
                "source_url": enc["url"],
                "error": str(e),
            })

    # Build metadata
    metadata = {
        "state": state_name,
        "slug": slug,
        "page_url": url,
        "title": title,
        "enclosures": pdf_files,
    }
    if state_name in index_summaries:
        metadata.update(index_summaries[state_name])

    # Write metadata
    with open(os.path.join(state_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    # Write letter text
    with open(os.path.join(state_dir, "letter.md"), "w") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Source:** {url}\n\n")
        f.write("---\n\n")
        f.write(letter_text)
        f.write("\n")

    print(f"  Saved metadata and letter for {state_name}")
    return metadata


def build_summary(all_metadata):
    """Build a summary JSON file with all states."""
    with open("summary.json", "w") as f:
        json.dump(all_metadata, f, indent=2)
    print(f"\nWrote summary.json with {len(all_metadata)} states")


def main():
    os.makedirs("states", exist_ok=True)

    # Scrape the index page
    index_summaries = scrape_index()
    print(f"Found {len(index_summaries)} states in index table")

    # Scrape each state
    all_metadata = []
    for slug, state_name in sorted(STATES.items()):
        try:
            meta = scrape_state(slug, state_name, index_summaries)
            all_metadata.append(meta)
        except Exception as e:
            print(f"  ERROR scraping {state_name}: {e}")
            all_metadata.append({"state": state_name, "slug": slug, "error": str(e)})

    # Build summary
    build_summary(all_metadata)
    print("\nDone!")


if __name__ == "__main__":
    main()
