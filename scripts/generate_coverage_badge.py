#!/usr/bin/env python3
"""
Generate coverage badge JSON for shields.io.

This script reads pytest-cov JSON output and generates a shields.io endpoint
JSON file that can be used to display a coverage badge in README.md.

Usage:
    python scripts/generate_coverage_badge.py --coverage-json coverage.json --output .github/badges/coverage.json
"""

import json
import argparse
import os
import sys
from pathlib import Path


def determine_color(coverage_percent: float) -> str:
    """Determine badge color based on coverage percentage."""
    if coverage_percent >= 90:
        return "brightgreen"
    elif coverage_percent >= 80:
        return "green"
    elif coverage_percent >= 70:
        return "yellowgreen"
    elif coverage_percent >= 60:
        return "yellow"
    elif coverage_percent >= 50:
        return "orange"
    else:
        return "red"


def main():
    parser = argparse.ArgumentParser(description="Generate shields.io coverage badge JSON")
    parser.add_argument(
        "--coverage-json",
        default="coverage.json",
        help="Path to pytest-cov JSON output file (default: coverage.json)",
    )
    parser.add_argument(
        "--output",
        default=".github/badges/coverage.json",
        help="Output path for shields.io JSON (default: .github/badges/coverage.json)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output")

    args = parser.parse_args()

    # Read coverage JSON
    try:
        with open(args.coverage_json, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Coverage file not found: {args.coverage_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.coverage_json}: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract coverage percentage
    try:
        coverage_percent = data["totals"]["percent_covered"]
        coverage_percent = round(coverage_percent, 2)
    except KeyError as e:
        print(f"Error: Missing expected key in coverage JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Coverage: {coverage_percent}%")

    # Determine badge color
    color = determine_color(coverage_percent)

    # Create badge JSON structure for shields.io endpoint
    badge_data = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{coverage_percent}%",
        "color": color,
        "namedLogo": "python",
    }

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write badge JSON
    with open(output_path, "w") as f:
        json.dump(badge_data, f, indent=2)

    if args.verbose:
        print(f"Generated badge JSON: {output_path}")
        print(
            f"Badge URL: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/jakob1379/canvas-code-correction/main/{args.output}"
        )

    # Print coverage percentage for logging
    print(f"Coverage percentage: {coverage_percent}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
