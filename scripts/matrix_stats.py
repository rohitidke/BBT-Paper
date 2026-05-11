#!/usr/bin/env python3
"""Compute matrix stats and write model_matrix_stats.txt in the same folder."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

import pandas as pd


def load_numeric_matrix(path: Path) -> pd.DataFrame:
    # Read without header first; many project matrices are plain numeric CSVs.
    df = pd.read_csv(path, header=None)

    # If first column is non-numeric labels (e.g., object names), drop it.
    first_col_numeric = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    if first_col_numeric.isna().all():
        df = df.iloc[:, 1:]

    # Coerce everything to numeric and binarize to 0/1 for robust zero checks.
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0)
    df = (df > 0).astype(int)
    return df


def parse_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_feature_name(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


def read_feature_names_from_base_matrix(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    if len(header) <= 1:
        return []
    return [str(h).strip() for h in header[1:]]


def read_feature_weights(path: Path) -> tuple[dict[str, float], list[float]]:
    if not path.exists():
        return {}, []
    weights: dict[str, float] = {}
    all_values: list[float] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feat = normalize_feature_name(row.get("features", ""))
            value = parse_float(row.get("normalized_freq"), 0.0)
            if feat:
                weights[feat] = value
            all_values.append(value)
    return weights, all_values


def infer_bmf_domain_level_branch(input_path: Path) -> tuple[str, str, str] | None:
    # Example:
    # output/experiments/bmf/animals/exemplar/frequency/preferred/1/reconstructed_matrix.csv
    # output/experiments/bmf/animals/category/all/preferred/8/reconstructed_matrix.csv
    parts = list(input_path.parts)
    if "bmf" not in parts:
        return None
    idx = parts.index("bmf")
    if len(parts) <= idx + 3:
        return None
    domain = parts[idx + 1]
    level = parts[idx + 2]
    branch = parts[idx + 3]
    return domain, level, branch


def infer_bmf_base_matrix_path(input_path: Path) -> Path | None:
    context = infer_bmf_domain_level_branch(input_path)
    if context is None:
        return None
    domain, level, branch = context

    if domain == "animals":
        if level == "category":
            return Path("data/animals/animal_feature_matrix_dichotomized.csv")
        if level == "exemplar":
            if branch in {"frequency", "importance", "random"}:
                base = Path(f"output/experiments/bmd/animals/exemplar/{branch}/data_matrix.csv")
            else:
                base = Path("data/animals/animal_exemplar_feature_matrix_dichotomized.csv")
            return base

    if domain == "artifacts":
        if level == "category":
            return Path("data/artifacts/artifact_category_feature_matrix_dichotomized.csv")
        if level == "exemplar":
            if branch in {"frequency", "importance", "random"}:
                base = Path(f"output/experiments/bmd/artifacts/exemplar/{branch}/data_matrix.csv")
            else:
                base = Path("data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv")
            return base

    return None


def compute_bmf_attribute_weight_metrics(
    input_path: Path,
    matrix: pd.DataFrame,
    attributes_non_zero: int,
    feature_freq_path: Path,
) -> tuple[str, str]:
    """
    Returns (average_attribute_freq_weight, average_top_n_attribute_freq_weight).
    Empty strings if data is unavailable.
    """
    base_matrix_path = infer_bmf_base_matrix_path(input_path)
    if base_matrix_path is None:
        return "", ""
    feature_weight_path = feature_freq_path

    feature_names = read_feature_names_from_base_matrix(base_matrix_path)
    weight_by_feature, all_weight_values = read_feature_weights(feature_weight_path)
    if not feature_names or not all_weight_values:
        return "", ""

    # Non-zero attributes in the provided matrix (0-based indexes).
    non_zero_indices = [int(i) for i, v in enumerate((matrix.sum(axis=0) > 0).tolist()) if v]

    selected_weights: list[float] = []
    for idx in non_zero_indices:
        if 0 <= idx < len(feature_names):
            key = normalize_feature_name(feature_names[idx])
            if key in weight_by_feature:
                selected_weights.append(float(weight_by_feature[key]))

    avg_selected = (sum(selected_weights) / len(selected_weights)) if selected_weights else 0.0

    n = max(0, int(attributes_non_zero))
    top_vals = sorted((float(v) for v in all_weight_values), reverse=True)[:n]
    avg_top_n = (sum(top_vals) / len(top_vals)) if top_vals else 0.0

    return f"{avg_selected:.6f}", f"{avg_top_n:.6f}"


def read_overall_jaccard_from_local_file(folder: Path) -> str:
    j_path = folder / "overall_jaccard.txt"
    if not j_path.exists():
        return ""
    for line in j_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("overall_jaccard="):
            return line.split("=", 1)[1].strip()
    return ""


def infer_bmf_run_context(input_path: Path) -> tuple[Path, str] | None:
    # Expected examples:
    # .../bmf/.../<run_id>/reconstructed_matrix.csv
    # .../bmf/.../preferred/<run_id>/reconstructed_matrix.csv
    if "bmf" not in input_path.parts:
        return None
    run_dir = input_path.parent

    if run_dir.parent.name == "preferred":
        run_id = run_dir.name
        runs_root = run_dir.parent.parent
        return runs_root, run_id

    if run_dir.name.isdigit():
        run_id = run_dir.name
        runs_root = run_dir.parent
        return runs_root, run_id

    return None


def infer_bmf_leaderboard_candidates(input_path: Path) -> tuple[list[Path], str] | None:
    context = infer_bmf_run_context(input_path)
    if context is None:
        return None
    runs_root, run_id = context
    run_dir = input_path.parent

    # If run is under .../preferred/<run_id>, prefer .../preferred/leaderboard.csv,
    # then fallback to branch-level leaderboard.
    if run_dir.parent.name == "preferred":
        return [
            run_dir.parent / "leaderboard.csv",
            run_dir.parent.parent / "leaderboard.csv",
        ], run_id

    return [runs_root / "leaderboard.csv"], run_id


def mark_selected_and_compute_medians(
    analysis_csv: Path,
    selected_labels: set[int],
) -> tuple[str, str]:
    if not analysis_csv.exists():
        return "", ""

    with analysis_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        return "", ""

    if "selected" not in fieldnames:
        fieldnames.append("selected")

    f1_vals: list[float] = []
    attr_vals: list[float] = []

    for row in rows:
        label = int(parse_float(row.get("label"), 0))
        is_selected = label in selected_labels
        row["selected"] = "true" if is_selected else "false"
        if is_selected:
            attr_vals.append(parse_float(row.get("mapped_feature_count"), 0.0))
            f1_vals.append(parse_float(row.get("dominant_f1_percent"), 0.0))

    with analysis_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    median_attr = f"{statistics.median(attr_vals):.6f}" if attr_vals else ""
    median_f1 = f"{statistics.median(f1_vals):.6f}" if f1_vals else ""
    return median_attr, median_f1


def read_bmf_selected_metrics(
    input_path: Path,
    leaderboard_override: Path | None = None,
) -> tuple[str, str, str]:
    """
    Returns (median_attribute_set_size, median_f1score, overall_jaccard).
    For non-BMF paths or missing files, returns empty strings.
    """
    inferred = infer_bmf_leaderboard_candidates(input_path)
    if inferred is None:
        return "", "", ""
    candidates, run_id = inferred

    if leaderboard_override is not None:
        candidates = [leaderboard_override]

    selected_labels: set[int] = set()
    overall_jaccard = ""
    found_row = False

    for leaderboard in candidates:
        if not leaderboard.exists():
            continue
        with leaderboard.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row.get("run_id", "")).strip() != str(run_id).strip():
                    continue
                overall_jaccard = str(row.get("overall_jaccard", "")).strip()
                raw = str(row.get("best_distinct_mapping", "")).strip()
                if raw:
                    try:
                        pairs = json.loads(raw)
                        for pair in pairs:
                            selected_labels.add(int(pair.get("label", 0)))
                    except Exception:
                        pass
                found_row = True
                break
        if found_row:
            break

    analysis_csv = input_path.parent / "label_category_analysis.csv"
    median_attr, median_f1 = mark_selected_and_compute_medians(analysis_csv, selected_labels)
    return median_attr, median_f1, overall_jaccard


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute matrix stats and write model_matrix_stats.txt."
    )
    parser.add_argument("--input", required=True, help="Path to matrix CSV file.")
    parser.add_argument(
        "--output-name",
        default="model_matrix_stats.txt",
        help="Output text filename (written in input file directory).",
    )
    parser.add_argument(
        "--feature-freq-path",
        default=None,
        help=(
            "Path to feature-frequency CSV (columns: features, normalized_freq). "
            "Required for BMF inputs."
        ),
    )
    parser.add_argument(
        "--leaderboard-path",
        default=None,
        help=(
            "Optional leaderboard.csv path for BMF selected-label and overall_jaccard lookup. "
            "If omitted, script infers candidate leaderboard paths."
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")
    feature_freq_override = Path(args.feature_freq_path) if args.feature_freq_path else None
    leaderboard_override = Path(args.leaderboard_path) if args.leaderboard_path else None
    if "bmf" in input_path.parts and feature_freq_override is None:
        raise ValueError("For BMF inputs, --feature-freq-path is required.")
    if feature_freq_override is not None and not feature_freq_override.exists():
        raise FileNotFoundError(f"Feature frequency CSV not found: {feature_freq_override}")
    if leaderboard_override is not None and not leaderboard_override.exists():
        raise FileNotFoundError(f"Leaderboard CSV not found: {leaderboard_override}")

    matrix = load_numeric_matrix(input_path)
    total_objects, total_attributes = matrix.shape

    empty_objects = int((matrix.sum(axis=1) == 0).sum())
    empty_attributes = int((matrix.sum(axis=0) == 0).sum())
    objects_non_zero = int(total_objects - empty_objects)
    attributes_non_zero = int(total_attributes - empty_attributes)
    attributes_relevance_ratio = (
        (attributes_non_zero / total_attributes) if total_attributes else 0.0
    )
    objects_relevance_ratio = (
        (objects_non_zero / total_objects) if total_objects else 0.0
    )

    average_attribute_freq_weight = ""
    average_top_n_attribute_freq_weight = ""

    # BMF-only metrics:
    median_attribute_set_size = ""
    median_f1score = ""
    overall_jaccard = ""
    if "bmf" in input_path.parts:
        (
            average_attribute_freq_weight,
            average_top_n_attribute_freq_weight,
        ) = compute_bmf_attribute_weight_metrics(
            input_path,
            matrix,
            attributes_non_zero,
            feature_freq_path=feature_freq_override,
        )
        median_attribute_set_size, median_f1score, overall_jaccard = read_bmf_selected_metrics(
            input_path,
            leaderboard_override=leaderboard_override,
        )
    elif "bmd" in input_path.parts:
        overall_jaccard = read_overall_jaccard_from_local_file(input_path.parent)

    output_path = input_path.parent / args.output_name
    output_path.write_text(
        "\n".join(
            [
                f"total_objects={total_objects}",
                f"total_attributes={total_attributes}",
                f"empty_objects_all_zero={empty_objects}",
                f"empty_attributes_all_zero={empty_attributes}",
                f"objects_non_zero={objects_non_zero}",
                f"attributes_non_zero={attributes_non_zero}",
                f"attributes_relevance_ratio={attributes_relevance_ratio:.6f}",
                f"objects_relevance_ratio={objects_relevance_ratio:.6f}",
                f"average_attribute_freq_weight={average_attribute_freq_weight}",
                f"top_n_average_attribute_freq_weight={average_top_n_attribute_freq_weight}",
                f"median_attribute_set_size={median_attribute_set_size}",
                f"median_f1score={median_f1score}",
                f"overall_jaccard={overall_jaccard}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
