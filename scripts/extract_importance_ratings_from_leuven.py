#!/usr/bin/env python3
"""Extract feature importance ratings from leuven_enhanced.json into four CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ANIMAL_CATEGORIES = ["birds", "fish", "insects", "mammals", "reptiles"]
ARTIFACT_CATEGORIES = [
    "kitchenutensils",
    "musicalinstruments",
    "tools",
    "weapons",
    "clothing",
    "vehicles",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read leuven_enhanced.json and write four CSVs with columns "
            "'features,category,importance_rating' for animals/artifacts x "
            "category/exemplar."
        )
    )
    parser.add_argument(
        "input_json",
        help="Path to data/leuven_enhanced.json",
    )
    return parser.parse_args()


def normalize_feature(text: str) -> str:
    return " ".join(str(text).strip().split())


def collect_importance_rows(
    judgments: dict,
    categories: list[str],
    importance_key: str,
) -> list[tuple[str, str, float]]:
    collected: list[tuple[str, str, float]] = []
    for category in categories:
        category_entry = judgments.get(category, {})
        attributes = category_entry.get("attributes", {})
        for attribute in attributes.values():
            label = normalize_feature(attribute.get("label_en", ""))
            importance = attribute.get("importance", {})
            rating_block = importance.get(importance_key, {})
            if not label or not isinstance(rating_block, dict) or "0" not in rating_block:
                continue
            try:
                rating = float(rating_block["0"])
            except (TypeError, ValueError):
                continue
            collected.append((label, category, rating))
    return collected


def aggregate_mean(rows: list[tuple[str, str, float]]) -> list[dict[str, str]]:
    values_by_feature_category: dict[tuple[str, str], list[float]] = defaultdict(list)
    for feature, category, rating in rows:
        values_by_feature_category[(feature, category)].append(rating)

    aggregated: list[dict[str, str]] = []
    for feature, category in sorted(
        values_by_feature_category,
        key=lambda item: (item[0].lower(), item[1].lower()),
    ):
        values = values_by_feature_category[(feature, category)]
        avg = sum(values) / len(values)
        aggregated.append(
            {
                "features": feature,
                "category": category,
                "importance_rating": f"{avg:.6f}",
            }
        )
    return aggregated


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["features", "category", "importance_rating"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    input_json = Path(args.input_json)
    if not input_json.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_json}")

    payload = json.loads(input_json.read_text(encoding="utf-8"))
    judgments = payload.get("exemplar_feature_judgments")
    if not isinstance(judgments, dict):
        raise ValueError("Missing or invalid 'exemplar_feature_judgments' in JSON.")

    outputs = [
        (
            collect_importance_rows(judgments, ANIMAL_CATEGORIES, "2"),
            Path("data/animals/importance_ratings_category.csv"),
        ),
        (
            collect_importance_rows(judgments, ANIMAL_CATEGORIES, "1"),
            Path("data/animals/importance_ratings_exemplar.csv"),
        ),
        (
            collect_importance_rows(judgments, ARTIFACT_CATEGORIES, "2"),
            Path("data/artifacts/importance_ratings_category.csv"),
        ),
        (
            collect_importance_rows(judgments, ARTIFACT_CATEGORIES, "1"),
            Path("data/artifacts/importance_ratings_exemplar.csv"),
        ),
    ]

    for raw_rows, out_path in outputs:
        aggregated_rows = aggregate_mean(raw_rows)
        write_csv(out_path, aggregated_rows)
        print(f"Wrote {len(aggregated_rows)} rows: {out_path}")


if __name__ == "__main__":
    main()
