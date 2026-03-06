# SNAP Food Restriction Waivers

Scraped data from the [USDA FNS SNAP Food Restriction Waivers](https://www.fns.usda.gov/snap/waivers/foodrestriction) page. Contains approval letters, terms and conditions, waiver requests, and supporting documents for all states with approved waivers.

## Quick Start

```bash
brew install tesseract  # macOS (or apt install tesseract-ocr on Linux)

git clone <repo-url>
cd waivers

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Updating Data

To re-scrape everything and rebuild all outputs in one command:

```bash
python3 scrape.py --full
```

This runs the full pipeline:

1. **`scrape.py`** -- Scrapes the USDA FNS index page, discovers all states with approved waivers, downloads each state's approval letter and PDF enclosures
2. **`extract.py`** -- Extracts markdown from each PDF (pymupdf4llm with Tesseract OCR fallback)
3. **`build_context.py`** -- Generates `all_waivers.md`, a single consolidated file with all waiver data

New states are automatically discovered from the index page -- no code changes needed.

You can also run each step individually:

```bash
python3 scrape.py          # Scrape pages and download PDFs only
python3 extract.py         # Extract markdown from PDFs and re-extract letters
python3 build_context.py   # Rebuild all_waivers.md
```

## Repository Structure

```
states/
  {state-slug}/
    metadata.json       # Structured data: state name, URLs, implementation date, summary, enclosure list
    letter.md           # Approval letter text from the state's page on fns.usda.gov
    *.pdf               # Original PDF enclosures (approval docs, terms & conditions, waiver requests)
    *.md                # Markdown extracted from each PDF (pymupdf4llm + OCR fallback)
summary.json            # All states' metadata in one file
all_waivers.md          # Consolidated markdown with all waiver data
scrape.py               # Scraper (auto-discovers states from USDA FNS index page)
extract.py              # PDF markdown extraction (pymupdf4llm + Tesseract OCR fallback)
build_context.py        # Generates all_waivers.md
```

## States Included

| State | Implementation Date | Restrictions |
|-------|-------------------|-------------|
| Arkansas | 07/01/26 | Soda, low-juice drinks, unhealthy drinks, candy |
| Colorado | 04/30/26 | Soft drinks |
| Florida | 04/20/26 | Soda, energy drinks, candy, prepared desserts |
| Hawaii | 08/01/26 | Soft drinks |
| Idaho | 02/15/26 | Soda, candy |
| Indiana | 01/01/26 | Soft drinks, candy |
| Iowa | 01/01/26 | All taxable food items (Iowa DOR definition) |
| Kansas | 02/15/27 | Candy, soft drinks |
| Louisiana | 02/18/26 | Soft drinks, energy drinks, candy |
| Missouri | 10/01/26 | Candy, prepared desserts, unhealthy beverages |
| Nebraska | 01/01/26 | Soda, energy drinks |
| Nevada | 02/01/28 | Candy, sugar-sweetened beverages |
| North Dakota | 09/01/26 | Soft drinks, energy drinks, candy |
| Ohio | 10/01/26 | Sugar-sweetened beverages |
| Oklahoma | 02/15/26 | Soft drinks, candy |
| South Carolina | 08/31/26 | Candy, energy drinks, soft drinks, sweetened beverages |
| Tennessee | 07/31/26 | Processed foods/beverages: soda, energy drinks, candy |
| Texas | 04/01/26 | Sweetened drinks, candy |
| Utah | 01/01/26 | Soft drinks |
| Virginia | 10/01/26 | Sweetened beverages |
| West Virginia | 01/01/26 | Soda |
| Wyoming | 02/01/27 | Sweetened carbonated beverages |

*This table reflects data at time of last scrape. Run `python3 scrape.py --full` to update.*

## Data Files

### metadata.json (per state)
```json
{
  "state": "Kansas",
  "slug": "kansas",
  "page_url": "https://www.fns.usda.gov/snap/waivers/foodrestriction/kansas",
  "title": "Kansas SNAP Food Restriction Waiver",
  "target_implementation_date": "02/15/27",
  "summary_of_request": "Restricts candy and soft drinks.",
  "enclosures": [
    {
      "title": "KS SNAP Food Restriction Waiver Approval",
      "filename": "ks-snapfoodrestrictionwaiver-approval.pdf",
      "source_url": "..."
    }
  ]
}
```

### letter.md (per state)
The approval letter from USDA Secretary Brooke L. Rollins to the state governor, including the terms of approval.

### *.md (extracted PDF markdown)
Markdown extracted from each PDF using pymupdf4llm, with Tesseract OCR fallback for pages with garbled text (e.g., USDA seal images). Preserves headers, bold, lists, and tables.

## Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Debian/Ubuntu)
- Python dependencies: `pip install -r requirements.txt` (`beautifulsoup4`, `requests`, `pymupdf`, `pymupdf4llm`, `pytesseract`, `Pillow`)

## Source

All data sourced from https://www.fns.usda.gov/snap/waivers/foodrestriction
