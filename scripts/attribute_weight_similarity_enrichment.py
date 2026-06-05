#!/usr/bin/env python3
"""Create attribute-level enriched similarity output from BMD/BMF matrix folders."""

from __future__ import annotations

import argparse
import csv
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from goodness import GoodnessType, compare_matrices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read data_matrix.csv and model_matrix.csv from an experiment folder and "
            "write attribute_weight_similarity_enriched.csv with column-wise Jaccard, "
            "normalized attribute frequency, category coverage, and model-bundle coverage."
        )
    )
    parser.add_argument(
        "input_dir",
        help="Folder containing data_matrix.csv and model_matrix.csv.",
    )
    parser.add_argument(
        "--freq-csv",
        default=None,
        help="Optional attribute-frequency CSV override.",
    )
    parser.add_argument(
        "--category-map-csv",
        default=None,
        help="Optional exemplar-to-category CSV override (default: typicality_ratings.csv for the domain).",
    )
    parser.add_argument(
        "--importance-csv",
        default=None,
        help="Optional importance-rating CSV override.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output CSV path (default: <input_dir>/attribute_weight_similarity_enriched.csv).",
    )
    return parser.parse_args()


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


def infer_domain(input_dir: Path) -> str:
    text = str(input_dir).lower()
    if "/animals/" in text or "/animal/" in text:
        return "animals"
    if "/artifacts/" in text or "/artifact/" in text:
        return "artifacts"
    raise ValueError(f"Could not infer domain from path: {input_dir}")


def infer_level(input_dir: Path) -> str:
    text = str(input_dir).lower()
    if "/category/" in text:
        return "category"
    if "/exemplar/" in text:
        return "exemplar"
    raise ValueError(f"Could not infer level from path: {input_dir}")


def default_freq_csv(domain: str, level: str) -> Path:
    if domain == "animals" and level == "category":
        return Path("data/animals/sum_features_freq_normalized.csv")
    if domain == "animals" and level == "exemplar":
        return Path("data/animals/sum_features_freq_normalized_exemplar.csv")
    if domain == "artifacts" and level == "category":
        return Path("data/artifacts/sum_features_freq_normalized_artifacts_category.csv")
    if domain == "artifacts" and level == "exemplar":
        return Path("data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv")
    raise ValueError(f"Unsupported domain/level combination: {domain}/{level}")


def default_category_map_csv(domain: str) -> Path:
    if domain == "animals":
        return Path("data/animals/typicality_ratings.csv")
    if domain == "artifacts":
        return Path("data/artifacts/typicality_ratings.csv")
    raise ValueError(f"Unsupported domain: {domain}")


def default_importance_csv(domain: str, level: str) -> Path:
    if domain == "animals" and level == "category":
        return Path("data/animals/importance_ratings_category.csv")
    if domain == "animals" and level == "exemplar":
        return Path("data/animals/importance_ratings_exemplar.csv")
    if domain == "artifacts" and level == "category":
        return Path("data/artifacts/importance_ratings_category.csv")
    if domain == "artifacts" and level == "exemplar":
        return Path("data/artifacts/importance_ratings_exemplar.csv")
    raise ValueError(f"Unsupported domain/level combination: {domain}/{level}")


def to_binary_int(text: str) -> int:
    value = str(text).strip()
    if not value:
        return 0
    try:
        return 1 if float(value) > 0 else 0
    except ValueError:
        return 0


def load_input_matrix(path: Path) -> tuple[list[str], list[str], np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows or len(rows[0]) < 2:
        raise ValueError(f"Invalid input CSV (needs header + at least 1 feature): {path}")

    features = [str(cell).strip() for cell in rows[0][1:]]
    objects: list[str] = []
    matrix_rows: list[list[int]] = []
    for row in rows[1:]:
        if not row:
            continue
        objects.append(str(row[0]).strip())
        numeric_cells = row[1:]
        matrix_rows.append([to_binary_int(value) for value in numeric_cells])

    incidences = np.asarray(matrix_rows, dtype=np.int32)
    return objects, features, incidences


def load_output_matrix(path: Path) -> np.ndarray:
    matrix_rows: list[list[int]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            matrix_rows.append([to_binary_int(value) for value in row])
    return np.asarray(matrix_rows, dtype=np.int32)


def normalize_text(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def normalize_category_key(value: str) -> str:
    return normalize_text(value).replace(" ", "")


def load_frequency_map(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        feature_key = "features" if "features" in fieldnames else "attribute"
        if feature_key not in fieldnames or "normalized_freq" not in fieldnames:
            raise ValueError(
                f"Frequency CSV must contain '{feature_key}' and 'normalized_freq': {path}"
            )

        result: dict[str, float] = {}
        for row in reader:
            feature = normalize_text(row.get(feature_key, ""))
            raw = str(row.get("normalized_freq", "")).strip()
            if not feature:
                continue
            try:
                result[feature] = float(raw)
            except ValueError:
                result[feature] = float("nan")
        return result


def load_object_category_map(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        if "exemplar" not in fieldnames or "category" not in fieldnames:
            raise ValueError(f"Category map CSV must contain exemplar and category columns: {path}")
        return {
            normalize_text(str(row.get("exemplar", ""))): str(row.get("category", "")).strip()
            for row in reader
            if str(row.get("exemplar", "")).strip()
        }


def load_importance_map(path: Path) -> dict[tuple[str, str], float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        required = {"features", "category", "importance_rating"}
        if not required.issubset(fieldnames):
            raise ValueError(
                f"Importance CSV must contain columns {sorted(required)}: {path}"
            )

        result: dict[tuple[str, str], float] = {}
        for row in reader:
            feature = normalize_text(row.get("features", ""))
            category = normalize_category_key(row.get("category", ""))
            raw = str(row.get("importance_rating", "")).strip()
            if not feature or not category:
                continue
            try:
                result[(feature, category)] = float(raw)
            except ValueError:
                result[(feature, category)] = float("nan")
        return result


def compute_row_bundle_ids(model_incidences: object) -> list[int]:
    bundle_by_pattern: dict[tuple[int, ...], int] = {}
    bundle_ids: list[int] = []
    for row in model_incidences:
        pattern = tuple(int(v) for v in row.tolist())
        if pattern not in bundle_by_pattern:
            bundle_by_pattern[pattern] = len(bundle_by_pattern) + 1
        bundle_ids.append(bundle_by_pattern[pattern])
    return bundle_ids


def format_float(value: float) -> str:
    if math.isnan(value):
        return ""
    return f"{value:.6f}"


def main() -> None:
    started = time.perf_counter()
    args = parse_args()
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    data_csv = input_dir / "data_matrix.csv"
    model_csv = input_dir / "model_matrix.csv"
    if not data_csv.exists():
        raise FileNotFoundError(f"Missing data_matrix.csv: {data_csv}")
    if not model_csv.exists():
        raise FileNotFoundError(f"Missing model_matrix.csv: {model_csv}")

    domain = infer_domain(input_dir)
    level = infer_level(input_dir)
    freq_csv = Path(args.freq_csv) if args.freq_csv else default_freq_csv(domain, level)
    category_map_csv = (
        Path(args.category_map_csv)
        if args.category_map_csv
        else default_category_map_csv(domain)
    )
    importance_csv = (
        Path(args.importance_csv)
        if args.importance_csv
        else default_importance_csv(domain, level)
    )
    if not freq_csv.exists():
        raise FileNotFoundError(f"Frequency CSV not found: {freq_csv}")
    if not category_map_csv.exists():
        raise FileNotFoundError(f"Category map CSV not found: {category_map_csv}")
    if not importance_csv.exists():
        raise FileNotFoundError(f"Importance CSV not found: {importance_csv}")

    objects, features, data_incidences = load_input_matrix(data_csv)
    model_incidences = load_output_matrix(model_csv)
    if data_incidences.shape != model_incidences.shape:
        raise ValueError(
            f"Matrix shape mismatch: data={data_incidences.shape}, model={model_incidences.shape}"
        )

    goodness = compare_matrices(data_incidences, model_incidences, GoodnessType.JACCARD)
    columnwise_similarity = goodness.columns
    if len(features) != len(columnwise_similarity):
        raise ValueError(
            f"Feature count ({len(features)}) does not match number of column scores "
            f"({len(columnwise_similarity)})"
        )

    feature_freq_map = load_frequency_map(freq_csv)
    object_category_map = load_object_category_map(category_map_csv)
    importance_map = load_importance_map(importance_csv)
    normalized_objects = [normalize_text(obj) for obj in objects]
    row_bundle_ids = compute_row_bundle_ids(model_incidences)

    rows: list[dict[str, str]] = []
    for col_idx, feature in enumerate(features):
        feature_key = normalize_text(feature)

        categories = sorted(
            {
                object_category_map[obj_key]
                for row_idx, obj_key in enumerate(normalized_objects)
                if data_incidences[row_idx, col_idx] > 0 and obj_key in object_category_map
            }
        )
        bundle_ids = sorted(
            {
                row_bundle_ids[row_idx]
                for row_idx in range(len(objects))
                if model_incidences[row_idx, col_idx] > 0
            }
        )
        bundle_text = ", ".join(str(bundle_id) for bundle_id in bundle_ids)
        bundle_specific_text = "True" if len(bundle_ids) == 1 else "False"
        normalized_freq_text = format_float(feature_freq_map.get(feature_key, float("nan")))
        similarity_text = format_float(float(columnwise_similarity[col_idx]))

        # Left join against category-specific importance ratings.
        # If an attribute belongs to multiple categories, emit one row per category.
        if categories:
            for category in categories:
                importance_value = importance_map.get(
                    (feature_key, normalize_category_key(category)),
                    float("nan"),
                )
                rows.append(
                    {
                        "attribute": feature,
                        "category": category,
                        "bundles": bundle_text,
                        "bundle_specific_attribute": bundle_specific_text,
                        "normalized_freq": normalized_freq_text,
                        "importance_rating": format_float(importance_value),
                        "columnwise_similarity": similarity_text,
                    }
                )
        else:
            rows.append(
                {
                    "attribute": feature,
                    "category": "",
                    "bundles": bundle_text,
                    "bundle_specific_attribute": bundle_specific_text,
                    "normalized_freq": normalized_freq_text,
                    "importance_rating": "",
                    "columnwise_similarity": similarity_text,
                }
            )

    output_path = (
        Path(args.out)
        if args.out
        else input_dir / "attribute_weight_similarity_enriched.csv"
    )
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "attribute",
                "category",
                "bundles",
                "bundle_specific_attribute",
                "normalized_freq",
                "importance_rating",
                "columnwise_similarity",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Input folder: {input_dir}")
    print(f"Domain/level: {domain}/{level}")
    print(f"Attributes processed: {len(rows)}")
    print(f"Wrote: {output_path}")
    elapsed = time.perf_counter() - started
    append_processing_duration(input_dir, "attribute_weight_similarity_enrichment.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
