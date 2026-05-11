#!/usr/bin/env python3
"""Create side-by-side Jaccard vs. typicality rankings for each category."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a typicality_similarity_enriched.csv file and write a CSV that "
            "compares descending Jaccard and typicality rankings side by side for "
            "each category."
        )
    )
    parser.add_argument(
        "input_csv",
        help="Path to typicality_similarity_enriched.csv",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Optional output CSV path. Defaults to "
            "<input_dir>/<input_stem>_jaccard_typicality_rankings.csv"
        ),
    )
    parser.add_argument(
        "--category-column",
        default="category",
        help="Category column name (default: category)",
    )
    parser.add_argument(
        "--item-column",
        default="exemplar",
        help="Item/exemplar column name (default: exemplar)",
    )
    parser.add_argument(
        "--jaccard-column",
        default="rowwise_similarity",
        help="Jaccard column name (default: rowwise_similarity)",
    )
    parser.add_argument(
        "--typicality-column",
        default="typicality_rating",
        help="Typicality column name (default: typicality_rating)",
    )
    return parser.parse_args()


def to_float(value: str) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def validate_columns(fieldnames: list[str] | None, required: set[str]) -> None:
    if fieldnames is None:
        raise ValueError("Input CSV does not have a header row.")
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")


def load_rows(
    csv_path: Path,
    category_column: str,
    item_column: str,
    jaccard_column: str,
    typicality_column: str,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        validate_columns(
            reader.fieldnames,
            {category_column, item_column, jaccard_column, typicality_column},
        )
        for row in reader:
            category = str(row[category_column]).strip()
            exemplar = str(row[item_column]).strip()
            grouped[category].append(
                {
                    "category": category,
                    "item": exemplar,
                    "jaccard": to_float(row[jaccard_column]),
                    "typicality": to_float(row[typicality_column]),
                }
            )
    return grouped


def descending_sort_key(row: dict[str, Any], metric: str) -> tuple[bool, float, str]:
    value = row[metric]
    return (value is None, -(value if value is not None else 0.0), row["item"].lower())


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def build_output_rows(grouped_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for category in sorted(grouped_rows):
        rows = grouped_rows[category]
        jaccard_ranked = sorted(rows, key=lambda row: descending_sort_key(row, "jaccard"))
        typicality_ranked = sorted(
            rows,
            key=lambda row: descending_sort_key(row, "typicality"),
        )

        for index in range(max(len(jaccard_ranked), len(typicality_ranked))):
            jaccard_row = jaccard_ranked[index] if index < len(jaccard_ranked) else None
            typicality_row = (
                typicality_ranked[index] if index < len(typicality_ranked) else None
            )
            output_rows.append(
                {
                    "category": category,
                    "jaccard_rank": str(index + 1) if jaccard_row else "",
                    "jaccard_exemplar": jaccard_row["item"] if jaccard_row else "",
                    "jaccard_index": (
                        format_number(jaccard_row["jaccard"]) if jaccard_row else ""
                    ),
                    "typicality_rank": str(index + 1) if typicality_row else "",
                    "typicality_exemplar": (
                        typicality_row["item"] if typicality_row else ""
                    ),
                    "typicality_rating": (
                        format_number(typicality_row["typicality"])
                        if typicality_row
                        else ""
                    ),
                }
            )
    return output_rows


def write_output(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "jaccard_rank",
        "jaccard_exemplar",
        "jaccard_index",
        "typicality_rank",
        "typicality_exemplar",
        "typicality_rating",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def default_output_path(input_csv: Path) -> Path:
    return input_csv.with_name(f"{input_csv.stem}_jaccard_typicality_rankings.csv")


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    grouped_rows = load_rows(
        input_csv,
        category_column=args.category_column,
        item_column=args.item_column,
        jaccard_column=args.jaccard_column,
        typicality_column=args.typicality_column,
    )
    output_rows = build_output_rows(grouped_rows)
    output_path = Path(args.out) if args.out else default_output_path(input_csv)
    write_output(output_rows, output_path)

    print(f"Read categories: {len(grouped_rows)}")
    print(f"Wrote ranking comparison: {output_path}")


if __name__ == "__main__":
    main()
