#!/usr/bin/env python3
"""
BMD wrapper for correlation analysis.

This script:
1. Reads data/model matrices from JSON.
2. Writes both matrices to CSV in a dynamic output folder under output/experiments/bmd.
3. Reuses scripts/correlation_analysis.py with those generated CSVs.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from correlation_analysis import main as run_correlation_analysis
from goodness import GoodnessType, compare_matrices


def parse_name_parts(path: Path) -> tuple[str, str]:
    """
    Parse matrix file stem into (domain, variant).

    Examples:
      animals_frequency.json -> (animals, frequency)
      animals_frequency_5.json -> (animals, frequency)
      artifacts_random.json -> (artifacts, random)
    """
    parts = path.stem.split("_")
    if len(parts) < 2:
        raise ValueError(
            f"Cannot infer domain/variant from filename: {path.name} "
            "(expected pattern like '<domain>_<variant>.json')."
        )
    domain = parts[0].strip()
    variant = parts[1].strip()
    if not domain or not variant:
        raise ValueError(f"Invalid domain/variant in filename: {path.name}")
    return domain, variant


def infer_output_subpath(variant: str) -> tuple[str, str]:
    """Map variant to output structure under output/experiments/bmd/<domain>/..."""
    v = variant.strip().lower()
    if v in {"frequency", "importance", "random"}:
        return "exemplar", v
    if v == "all":
        return "category", "all"
    # Fallback: keep unknown variants under exemplar for backward compatibility.
    return "exemplar", v


def load_matrix_json(path: Path) -> tuple[list[str], list[str], list[list[int]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON matrix format in {path}: expected object.")

    objects = payload.get("objects")
    features = payload.get("features")
    incidences = payload.get("incidences")

    if not isinstance(objects, list) or not isinstance(features, list) or not isinstance(incidences, list):
        raise ValueError(
            f"Invalid JSON matrix format in {path}: "
            "expected keys objects/features/incidences as lists."
        )

    object_names = [str(x).strip() for x in objects]
    feature_names = [str(x).strip() for x in features]
    matrix: list[list[int]] = []
    n_cols = len(feature_names)

    if len(incidences) != len(object_names):
        raise ValueError(
            f"Row count mismatch in {path}: objects={len(object_names)} vs incidences={len(incidences)}"
        )

    for idx, row in enumerate(incidences, start=1):
        if not isinstance(row, list):
            raise ValueError(f"Invalid row type in {path} at row {idx}: expected list.")
        if len(row) != n_cols:
            raise ValueError(
                f"Column count mismatch in {path} at row {idx}: "
                f"expected {n_cols}, got {len(row)}"
            )
        matrix.append([1 if int(v) > 0 else 0 for v in row])

    return object_names, feature_names, matrix


def write_data_matrix_csv(path: Path, objects: list[str], features: list[str], incidences: list[list[int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["object", *features])
        for name, row in zip(objects, incidences):
            writer.writerow([name, *row])


def write_model_matrix_csv(path: Path, incidences: list[list[int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(incidences)


def default_typicality_path(domain: str) -> Path:
    domain_key = domain.strip().lower()
    if domain_key.startswith("animal"):
        return Path("data/animals/typicality_ratings.csv")
    if domain_key.startswith("artifact"):
        return Path("data/artifacts/typicality_ratings.csv")
    raise ValueError(
        f"Cannot infer typicality file for domain '{domain}'. "
        "Use a filename starting with 'animal' or 'artifact(s)'."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BMD correlation analysis from JSON matrices.")
    parser.add_argument(
        "--data-matrix",
        required=True,
        help="Path to data matrix JSON, e.g. data/bmd/data_matrix/animals_frequency.json",
    )
    parser.add_argument(
        "--model-matrix",
        required=True,
        help="Path to model matrix JSON, e.g. data/bmd/model_matrix/animals_frequency_5.json",
    )
    args = parser.parse_args()

    data_json = Path(args.data_matrix)
    model_json = Path(args.model_matrix)

    if not data_json.exists():
        raise FileNotFoundError(f"Data matrix JSON not found: {data_json}")
    if not model_json.exists():
        raise FileNotFoundError(f"Model matrix JSON not found: {model_json}")

    data_domain, data_variant = parse_name_parts(data_json)
    model_domain, model_variant = parse_name_parts(model_json)
    if data_domain != model_domain:
        raise ValueError(
            f"Domain mismatch: data={data_domain} vs model={model_domain}"
        )
    if data_variant != model_variant:
        raise ValueError(
            f"Variant mismatch: data={data_variant} vs model={model_variant}"
        )

    data_objects, data_features, data_inc = load_matrix_json(data_json)
    model_objects, model_features, model_inc = load_matrix_json(model_json)

    if len(data_objects) != len(model_objects):
        raise ValueError(
            f"Row mismatch between data/model JSON: {len(data_objects)} vs {len(model_objects)}"
        )
    if len(data_features) != len(model_features):
        raise ValueError(
            f"Column mismatch between data/model JSON: {len(data_features)} vs {len(model_features)}"
        )

    level, branch = infer_output_subpath(data_variant)
    out_dir = Path("output/experiments/bmd") / data_domain / level / branch
    out_dir.mkdir(parents=True, exist_ok=True)

    data_csv = out_dir / "data_matrix.csv"
    model_csv = out_dir / "model_matrix.csv"
    write_data_matrix_csv(data_csv, data_objects, data_features, data_inc)
    write_model_matrix_csv(model_csv, model_inc)

    # Store the same overall Jaccard used by correlation_analysis.
    overall_jaccard = float(
        compare_matrices(
            np.asarray(data_inc, dtype=np.int32),
            np.asarray(model_inc, dtype=np.int32),
            GoodnessType.JACCARD,
        ).total
    )
    overall_txt = out_dir / "overall_jaccard.txt"
    overall_txt.write_text(f"overall_jaccard={overall_jaccard:.6f}\n", encoding="utf-8")

    print(f"Data CSV written:  {data_csv}")
    print(f"Model CSV written: {model_csv}")
    print(f"Overall Jaccard:   {overall_jaccard:.6f}")
    print(f"Jaccard file:      {overall_txt}")

    typicality = default_typicality_path(data_domain)
    if not typicality.exists():
        raise FileNotFoundError(f"Typicality CSV not found: {typicality}")

    print("Running correlation analysis...")
    run_correlation_analysis(
        input_path=str(data_csv),
        output_path=str(model_csv),
        typicality_path=str(typicality),
        domain=("artifacts" if data_domain.lower().startswith("artifact") else "animal"),
        similarity_measure="jaccard",
        exclude=False,
        run_id=None,
        runs_root=None,
    )

    print(f"\nFinished. Results available in: {out_dir}")
    print(f"- {out_dir / 'correlation_analysis_results.csv'}")
    print(f"- {out_dir / 'typicality_similarity_enriched.csv'}")


if __name__ == "__main__":
    main()
