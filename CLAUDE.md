# SNAP Food Restriction Waivers Project

Scraped data from the USDA FNS website on SNAP food restriction waivers across 22 U.S. states.

## Project Structure

- `summary.json` — Index of all 22 states with metadata (state name, slug, page URL, enclosure PDFs, implementation date, restriction summary)
- `states/<slug>/` — Per-state directory containing:
  - `metadata.json` — Same fields as the state's entry in summary.json
  - `letter.md` — Approval letter scraped from the state's FNS page
  - `*.pdf` — Downloaded enclosure PDFs (approval letters, waiver requests, modifications, retailer notices)
  - `*.md` — Markdown extracted from each PDF (via pymupdf4llm with Tesseract OCR fallback)
- `scrape.py` — Scraper that downloads state pages, letters, and PDFs
- `extract.py` — PDF markdown extraction script (pymupdf4llm + Tesseract OCR fallback + post-processing)
- `build_context.py` — Generates `all_waivers.md` from all scraped data
- `all_waivers.md` — Single consolidated markdown file with all waiver data (~175K tokens)

## States Covered

Arkansas, Colorado, Florida, Hawaii, Idaho, Indiana, Iowa, Kansas, Louisiana, Missouri, Nebraska, Nevada, North Dakota, Ohio, Oklahoma, South Carolina, Tennessee, Texas, Utah, Virginia, West Virginia, Wyoming
