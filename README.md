# SNAP Food Restriction Waivers

Scraped data from the [USDA FNS SNAP Food Restriction Waivers](https://www.fns.usda.gov/snap/waivers/foodrestriction) page. Contains approval letters, terms and conditions, waiver requests, and supporting documents for all 22 states with approved waivers.

## Repository Structure

```
states/
  {state-slug}/
    metadata.json       # Structured data: state name, URLs, implementation date, summary, enclosure list
    letter.md           # Approval letter text from the state's page on fns.usda.gov
    *.pdf               # Original PDF enclosures (approval docs, terms & conditions, waiver requests)
    *.txt               # Machine-readable text extracted from each PDF
summary.json            # All states' metadata in one file
scrape.py               # Script to scrape state pages and download PDFs
extract.py              # Script to extract letter text and PDF text
```

## States Included (22)

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

### *.txt (extracted PDF text)
Plain text extracted from each PDF for full-text search and AI analysis. Includes page markers.

## Refreshing Data

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scrape.py    # Scrape pages and download PDFs
python3 extract.py   # Extract text from PDFs and re-extract letters
```

## Source

All data sourced from https://www.fns.usda.gov/snap/waivers/foodrestriction (accessed March 2026).
