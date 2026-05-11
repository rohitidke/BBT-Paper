#!/usr/bin/env python3
"""
Run BMD correlation analysis starting from existing CSV matrices.

This script skips JSON -> CSV generation and starts from:
- data_matrix.csv (with first column as object names)
- model_matrix.csv (no header)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from correlation_analysis import (
    load_input_csv,
    load_output_csv,
    main as run_correlation_analysis,
)
from goodness import GoodnessType, compare_matrices


def infer_domain_from_path(path: Path) -> str:
    text = str(path).lower()
    if "/animals/" in text or "/animal/" in text:
        return "animal"
    if "/artifacts/" in text or "/artifact/" in text:
        return "artifacts"
    raise ValueError(
        "Cannot infer domain from path. Pass --domain explicitly (animal or artifacts)."
    )


def default_typicality_path(domain: str) -> Path:
    d = domain.strip().lower()
    if d.startswith("animal"):
        return Path("data/animals/typicality_ratings.csv")
    if d.startswith("artifact"):
        return Path("data/artifacts/typicality_ratings.csv")
    raise ValueError(f"Unsupported domain: {domain}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run correlation analysis from existing BMD CSV matrices."
    )
    parser.add_argument(
        "--data-csv",
        required=True,
        help="Path to data_matrix.csv (first column = object names).",
    )
    parser.add_argument(
        "--model-csv",
        required=True,
        help="Path to model_matrix.csv (no header).",
    )
    parser.add_argument(
        "--domain",
        default=None,
        choices=["animal", "animals", "artifact", "artifacts"],
        help="Optional domain override. If omitted, inferred from paths.",
    )
    parser.add_argument(
        "--typicality-path",
        default=None,
        help="Optional typicality CSV path. If omitted, inferred from domain.",
    )
    parser.add_argument(
        "--similarity-measure",
        default="jaccard",
        choices=["jaccard", "ruzicka", "czekanowski"],
        help="Similarity measure for correlation analysis (default: jaccard).",
    )
    parser.add_argument(
        "--exclude",
        action="store_true",
        help="Enable domain-specific exemplar exclusions (default: False).",
    )
    args = parser.parse_args()

    data_csv = Path(args.data_csv)
    model_csv = Path(args.model_csv)
    if not data_csv.exists():
        raise FileNotFoundError(f"Data CSV not found: {data_csv}")
    if not model_csv.exists():
        raise FileNotFoundError(f"Model CSV not found: {model_csv}")

    if args.domain:
        domain = "artifacts" if args.domain.startswith("artifact") else "animal"
    else:
        domain = infer_domain_from_path(data_csv)

    typicality = (
        Path(args.typicality_path)
        if args.typicality_path
        else default_typicality_path(domain)
    )
    if not typicality.exists():
        raise FileNotFoundError(f"Typicality CSV not found: {typicality}")

    # Compute and store overall Jaccard from the CSV matrices.
    _, data_inc = load_input_csv(data_csv)
    model_inc = load_output_csv(model_csv)
    if data_inc.shape != model_inc.shape:
        raise ValueError(
            f"Matrix shape mismatch: data={data_inc.shape}, model={model_inc.shape}"
        )

    overall_jaccard = float(
        compare_matrices(data_inc, model_inc, GoodnessType.JACCARD).total
    )
    out_dir = model_csv.parent
    overall_txt = out_dir / "overall_jaccard.txt"
    overall_txt.write_text(f"overall_jaccard={overall_jaccard:.6f}\n", encoding="utf-8")

    print(f"Overall Jaccard: {overall_jaccard:.6f}")
    print(f"Wrote: {overall_txt}")

    print("Running correlation analysis...")
    run_correlation_analysis(
        input_path=str(data_csv),
        output_path=str(model_csv),
        typicality_path=str(typicality),
        domain=domain,
        similarity_measure=args.similarity_measure,
        exclude=args.exclude,
        run_id=None,
        runs_root=None,
    )


if __name__ == "__main__":
    main()

