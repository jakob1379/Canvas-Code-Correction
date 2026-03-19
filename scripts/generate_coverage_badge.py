#!/usr/bin/env python3
"""
Generate coverage badge JSON for shields.io.

This script reads pytest-cov JSON output and generates a shields.io endpoint
JSON file that can be used to display a coverage badge in README.md.

Usage:
    python scripts/generate_coverage_badge.py --coverage-json coverage.json --output .github/badges/coverage.json
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Sequence

BadgeColor = Literal["brightgreen", "green", "yellowgreen", "yellow", "orange", "red"]


@dataclass(frozen=True)
class CoverageTotals:
    percent_covered: float


@dataclass(frozen=True)
class CoverageReport:
    totals: CoverageTotals

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CoverageReport":
        totals = data.get("totals")
        if not isinstance(totals, dict):
            raise RuntimeError("Missing expected key in coverage JSON: 'totals'")

        percent_covered = totals.get("percent_covered")
        if percent_covered is None:
            raise RuntimeError("Missing expected key in coverage JSON: 'percent_covered'")
        if not isinstance(percent_covered, int | float):
            raise RuntimeError("Coverage percentage must be numeric")

        return cls(totals=CoverageTotals(percent_covered=float(percent_covered)))


@dataclass(frozen=True)
class BadgeData:
    schemaVersion: int
    label: str
    message: str
    color: str
    namedLogo: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def determine_color(coverage_percent: float) -> BadgeColor:
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


def load_coverage_percent(coverage_path: Path) -> float:
    try:
        with coverage_path.open("r") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Coverage file not found: {coverage_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {coverage_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Coverage JSON root must be an object")

    report = CoverageReport.from_dict(data)

    return round(report.totals.percent_covered, 2)


def main(argv: Sequence[str] | None = None) -> int:
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

    args = parser.parse_args(argv)

    try:
        coverage_percent = load_coverage_percent(Path(args.coverage_json))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Coverage: {coverage_percent}%")

    color = determine_color(coverage_percent)
    badge_data = BadgeData(
        schemaVersion=1,
        label="coverage",
        message=f"{coverage_percent}%",
        color=color,
        namedLogo="python",
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(badge_data.to_dict(), f, indent=2)

    if args.verbose:
        print(f"Generated badge JSON: {output_path}")
        print(
            f"Badge URL: https://img.shields.io/endpoint?url=https://ccc.jgalabs.dk/badges/coverage.json"
        )

    print(f"Coverage percentage: {coverage_percent}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
