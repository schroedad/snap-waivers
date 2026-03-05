#!/usr/bin/env python3
"""Build a single consolidated markdown file from all scraped SNAP waiver data."""

import json
import os
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
        parts.append("")
        parts.append("### Approval Letter")
        parts.append("")
        parts.append(letter_path.read_text().strip())

    # Enclosure text files
    txt_files = sorted(state_dir.glob("*.txt"))
    for txt_file in txt_files:
        parts.append("")
        parts.append(f"### Enclosure: {txt_file.stem}")
        parts.append("")
        parts.append(txt_file.read_text().strip())

    return "\n".join(parts)


def main():
    states = load_summary()
    # Sort alphabetically by state name
    states.sort(key=lambda s: s["state"])

    sections = []

    # Title and intro
    sections.append("# SNAP Food Restriction Waivers — All States")
    sections.append("")
    sections.append(
        "This document contains all publicly available data on SNAP food restriction waivers "
        "across 22 U.S. states, including approval letters, waiver requests, modifications, "
        "and retailer notices. Data was scraped from the USDA Food and Nutrition Service website."
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

    # Token estimate (~4 chars per token)
    char_count = len(output)
    token_estimate = char_count // 4
    print(f"Generated {OUTPUT_FILE}")
    print(f"  {char_count:,} characters")
    print(f"  ~{token_estimate:,} tokens (rough estimate)")


if __name__ == "__main__":
    main()
