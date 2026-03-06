#!/usr/bin/env python3
"""Build a single consolidated markdown file from all scraped SNAP waiver data."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
STATES_DIR = ROOT / "states"
SUMMARY_FILE = ROOT / "summary.json"
OUTPUT_FILE = ROOT / "all_waivers.md"


def load_summary():
    with open(SUMMARY_FILE) as f:
        return json.load(f)


def build_summary_table(states):
    lines = [
        "| State | Implementation Date | Restrictions |",
        "|-------|-------------------|--------------|",
    ]
    for s in states:
        lines.append(f"| {s['state']} | {s['target_implementation_date']} | {s['summary_of_request']} |")
    return "\n".join(lines)


def strip_letter_header(text):
    """Strip the internal header/source/divider from letter.md content."""
    # Remove leading "# Title\n\n**Source:** ...\n\n---\n\n"
    text = re.sub(
        r'^#\s+[^\n]+\n+\*\*Source:\*\*[^\n]*\n+---\n+',
        '',
        text,
        count=1,
    )
    return text.strip()


def strip_enclosure_header(text):
    """Strip the internal header/source/divider from enclosure .md content."""
    text = re.sub(
        r'^#\s+[^\n]+\n+\*\*Source:\*\*[^\n]*\n+---\n+',
        '',
        text,
        count=1,
    )
    return text.strip()


def strip_cover_letter_from_enclosure(text):
    """Strip content before WAIVER SUMMARY heading in approval PDFs.

    The cover letter (page 1) is already included via letter.md from the
    HTML-scraped version, which is cleaner. For approval PDFs, skip
    everything before the first major heading like "WAIVER SUMMARY",
    "Terms and Conditions", or "TERMS AND CONDITIONS".
    """
    # Look for common headings that start the substantive content
    patterns = [
        r'(?m)^#+\s*WAIVER\s+SUMMARY',
        r'(?m)^#+\s*Terms\s+and\s+Conditions',
        r'(?m)^#+\s*TERMS\s+AND\s+CONDITIONS',
        r'(?m)^\*\*WAIVER\s+SUMMARY\*\*',
        r'(?m)^\*\*Terms\s+and\s+Conditions\*\*',
        r'(?m)^\*\*TERMS\s+AND\s+CONDITIONS\*\*',
        r'(?m)^WAIVER\s+SUMMARY',
        r'(?m)^Terms\s+and\s+Conditions',
        r'(?m)^TERMS\s+AND\s+CONDITIONS',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return text[match.start():].strip()
    return text


def build_state_section(entry):
    slug = entry["slug"]
    state_dir = STATES_DIR / slug
    parts = []

    # Header
    parts.append(f"## State: {entry['state']}")

    # Metadata
    parts.append("")
    parts.append("### Metadata")
    parts.append(f"- **Implementation Date:** {entry['target_implementation_date']}")
    parts.append(f"- **Summary:** {entry['summary_of_request']}")
    parts.append(f"- **Source Page:** {entry['page_url']}")

    # Approval letter
    letter_path = state_dir / "letter.md"
    if letter_path.exists():
        letter_content = strip_letter_header(letter_path.read_text())
        parts.append("")
        parts.append("### Approval Letter")
        parts.append("")
        parts.append(letter_content)

    # Enclosure markdown files (excluding letter.md)
    md_files = sorted(state_dir.glob("*.md"))
    for md_file in md_files:
        if md_file.name == "letter.md":
            continue
        raw = md_file.read_text().strip()
        content = strip_enclosure_header(raw)

        # For approval PDFs, strip the duplicate cover letter
        if "approval" in md_file.stem.lower():
            content = strip_cover_letter_from_enclosure(content)

        parts.append("")
        parts.append(f"### Enclosure: {md_file.stem}")
        parts.append("")
        parts.append(content)

    return "\n".join(parts)


def main():
    states = load_summary()
    states.sort(key=lambda s: s["state"])

    sections = []

    # Title and intro
    sections.append("# SNAP Food Restriction Waivers — All States")
    sections.append("")
    sections.append(
        f"This document contains all publicly available data on SNAP food restriction waivers "
        f"across {len(states)} U.S. states, including approval letters, waiver requests, modifications, "
        f"and retailer notices. Data was scraped from the USDA Food and Nutrition Service website."
    )

    # Summary table
    sections.append("")
    sections.append("## Summary Table")
    sections.append("")
    sections.append(build_summary_table(states))

    # Individual state sections
    for entry in states:
        sections.append("")
        sections.append("---")
        sections.append("")
        sections.append(build_state_section(entry))

    output = "\n".join(sections) + "\n"
    OUTPUT_FILE.write_text(output)

    char_count = len(output)
    token_estimate = char_count // 4
    print(f"Generated {OUTPUT_FILE}")
    print(f"  {char_count:,} characters")
    print(f"  ~{token_estimate:,} tokens (rough estimate)")


if __name__ == "__main__":
    main()
