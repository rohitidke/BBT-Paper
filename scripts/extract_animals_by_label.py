#!/usr/bin/env python3
"""Analyze MATLAB label bundles against ground-truth categories across experiments."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RUNS_ROOT = "output/experiments/bmf/animals/category/all"


def normalize_key(text: str) -> str:
    return text.strip().lower()


def read_animals_and_features(animal_csv: Path) -> tuple[list[str], list[str]]:
    with animal_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None or len(header) < 2:
            raise ValueError(f"Invalid animal matrix CSV: {animal_csv}")
        animals: list[str] = []
        for row in reader:
            if not row:
                continue
            animals.append(row[0].strip())
    feature_names = [h.strip() for h in header[1:]]
    return animals, feature_names


def read_feature_weights(feature_freq_csv: Path) -> dict[str, float]:
    weights: dict[str, float] = {}
    with feature_freq_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feature = normalize_key(row["features"])
            value = float(row["normalized_freq"])
            weights[feature] = value
    return weights


def read_categories(typicality_csv: Path) -> tuple[dict[str, str], Counter[str]]:
    exemplar_to_category: dict[str, str] = {}
    with typicality_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            exemplar = row["exemplar"].strip()
            category = row["category"].strip()
            if exemplar in exemplar_to_category and exemplar_to_category[exemplar] != category:
                raise ValueError(
                    f"Inconsistent category for exemplar '{exemplar}': "
                    f"{exemplar_to_category[exemplar]} vs {category}"
                )
            exemplar_to_category[exemplar] = category

    category_totals: Counter[str] = Counter(exemplar_to_category.values())
    return exemplar_to_category, category_totals


def read_label_membership(label_csv: Path) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    rows_by_label: dict[int, set[int]] = defaultdict(set)
    cols_by_label: dict[int, set[int]] = defaultdict(set)
    with label_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = int(row["label"])
            # Preprocessing rule: always ignore background label 1.
            if label == 1:
                continue
            row_orig = int(row["row_orig"])
            col_orig = int(row["col_orig"])
            rows_by_label[label].add(row_orig)
            cols_by_label[label].add(col_orig)
    return rows_by_label, cols_by_label


def label_to_animals(
    rows_by_label: dict[int, set[int]], animals: list[str], skip_label: int | None
) -> dict[int, list[str]]:
    label_animals: dict[int, list[str]] = {}
    total = len(animals)
    for label in sorted(rows_by_label):
        if skip_label is not None and label == skip_label:
            continue
        names: list[str] = []
        for idx in sorted(rows_by_label[label]):
            if 1 <= idx <= total:
                names.append(animals[idx - 1])  # MATLAB index -> Python index
        label_animals[label] = names
    return label_animals


def format_animals_output(label_animals: dict[int, list[str]]) -> str:
    lines: list[str] = []
    for label in sorted(label_animals):
        lines.append(f"Label {label}:")
        for animal in label_animals[label]:
            lines.append(animal)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def analyze_label_categories(
    label_animals: dict[int, list[str]],
    exemplar_to_category: dict[str, str],
    category_totals: Counter[str],
    cols_by_label: dict[int, set[int]],
    feature_names: list[str],
    feature_weights: dict[str, float],
) -> tuple[str, list[dict[str, Any]], dict[int, Counter[str]], list[str]]:
    lines: list[str] = []
    category_names = sorted(set(exemplar_to_category.values()))
    rows: list[dict[str, Any]] = []
    counts_by_label: dict[int, Counter[str]] = {}

    for label in sorted(label_animals):
        animals = label_animals[label]
        counts: Counter[str] = Counter()
        for animal in animals:
            counts[exemplar_to_category.get(animal, "unknown")] += 1
        counts_by_label[label] = counts

        total = len(animals)
        if total == 0:
            dominant_category = "none"
            dominant_count = 0
            purity = 0.0
            gt_total = 0
            dominant_recall = 0.0
            dominant_f1 = 0.0
        else:
            dominant_category, dominant_count = counts.most_common(1)[0]
            purity = 100.0 * dominant_count / total
            gt_total = int(category_totals.get(dominant_category, 0))
            dominant_recall = 100.0 * dominant_count / gt_total if gt_total else 0.0
            denom = purity + dominant_recall
            dominant_f1 = (2.0 * purity * dominant_recall / denom) if denom > 0 else 0.0

        feature_indices = sorted(cols_by_label.get(label, set()))
        feature_values: list[float] = []
        for feature_idx in feature_indices:
            if 1 <= feature_idx <= len(feature_names):
                feature_name = normalize_key(feature_names[feature_idx - 1])
                if feature_name in feature_weights:
                    feature_values.append(float(feature_weights[feature_name]))
        n_features = len(feature_indices)
        mapped_features = len(feature_values)
        avg_feature_weight = (
            (sum(feature_values) / mapped_features) if mapped_features else 0.0
        )

        lines.append(f"Label {label} (n={total}):")
        for category in category_names:
            lines.append(f"{category}: {counts.get(category, 0)}")
        if counts.get("unknown", 0):
            lines.append(f"unknown: {counts['unknown']}")
        lines.append(
            "dominant: "
            f"{dominant_category} ({dominant_count}/{total}, purity={purity:.1f}%, "
            f"recall={dominant_count}/{gt_total}={dominant_recall:.1f}%, "
            f"f1={dominant_f1:.1f}%)"
        )
        lines.append(
            "avg_feature_freq_weight: "
            f"{avg_feature_weight:.4f} (mapped_features={mapped_features}/{n_features})"
        )
        lines.append("")

        row: dict[str, Any] = {
            "label": label,
            "n_animals": total,
            "dominant_category": dominant_category,
            "dominant_count": dominant_count,
            "dominant_category_total": gt_total,
            "purity_percent": round(purity, 2),
            "dominant_recall_percent": round(dominant_recall, 2),
            "dominant_f1_percent": round(dominant_f1, 2),
            "n_features": n_features,
            "mapped_feature_count": mapped_features,
            "avg_feature_freq_weight": round(avg_feature_weight, 6),
        }
        for category in category_names:
            row[category] = counts.get(category, 0)
        row["unknown"] = counts.get("unknown", 0)
        rows.append(row)

    return "\n".join(lines).rstrip() + "\n", rows, counts_by_label, category_names


def write_analysis_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def best_distinct_mapping(
    counts_by_label: dict[int, Counter[str]],
    category_names: list[str],
) -> tuple[int, list[dict[str, Any]]]:
    labels = sorted(counts_by_label)
    categories = list(category_names)
    if not labels or not categories:
        return 0, []

    if len(labels) < len(categories):
        mapped_count = len(labels)
        category_sets = itertools.combinations(categories, mapped_count)
    else:
        mapped_count = len(categories)
        category_sets = [tuple(categories)]

    best_score = -1
    best_pairs: list[dict[str, Any]] = []

    for cat_set in category_sets:
        for label_combo in itertools.combinations(labels, mapped_count):
            for cat_perm in itertools.permutations(cat_set, mapped_count):
                score = 0
                pairs: list[dict[str, Any]] = []
                for label, category in zip(label_combo, cat_perm):
                    matched = counts_by_label[label].get(category, 0)
                    score += matched
                    pairs.append(
                        {"category": category, "label": label, "matched_count": matched}
                    )
                if score > best_score:
                    best_score = score
                    best_pairs = sorted(pairs, key=lambda x: str(x["category"]))

    return max(0, best_score), best_pairs


def best_category_first_mapping_by_feature_weight(
    counts_by_label: dict[int, Counter[str]],
    category_names: list[str],
    analysis_rows: list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]]]:
    """Pick one label per category using highest avg feature weight among present labels."""
    labels = sorted(counts_by_label)
    if not labels or not category_names:
        return 0, []

    avg_feature_weight_by_label = {
        int(row["label"]): float(row.get("avg_feature_freq_weight", 0.0))
        for row in analysis_rows
    }
    purity_by_label = {
        int(row["label"]): float(row.get("purity_percent", 0.0)) for row in analysis_rows
    }

    pairs: list[dict[str, Any]] = []
    total_matched = 0

    for category in category_names:
        present_candidates: list[tuple[float, int, float, int]] = []
        for label in labels:
            matched = int(counts_by_label[label].get(category, 0))
            if matched > 0:
                present_candidates.append(
                    (
                        float(avg_feature_weight_by_label.get(label, 0.0)),
                        matched,
                        float(purity_by_label.get(label, 0.0)),
                        -label,
                    )
                )

        if present_candidates:
            best_key = max(present_candidates)
            selected_label = -best_key[3]
            matched_count = int(counts_by_label[selected_label].get(category, 0))
        else:
            # Fallback: if category is absent in all labels, select label with best avg weight.
            selected_label = max(
                labels,
                key=lambda lb: (
                    float(avg_feature_weight_by_label.get(lb, 0.0)),
                    float(purity_by_label.get(lb, 0.0)),
                    -lb,
                ),
            )
            matched_count = 0

        pairs.append(
            {
                "category": category,
                "label": int(selected_label),
                "matched_count": int(matched_count),
            }
        )
        total_matched += int(matched_count)

    pairs = sorted(pairs, key=lambda x: str(x["category"]))
    return total_matched, pairs


def best_dominant_category_mapping_with_filters(
    counts_by_label: dict[int, Counter[str]],
    category_names: list[str],
    analysis_rows: list[dict[str, Any]],
    min_dominant_count: int = 5,
    min_mapped_feature_count: int = 1,
) -> tuple[int, list[dict[str, Any]]]:
    """
    Category-first mapping with distinct labels:
    1) candidates are labels with dominant_category == category
    2) reject weak labels (dominant_count < min_dominant_count or
       mapped_feature_count < min_mapped_feature_count)
    3) among remaining candidates choose highest avg_feature_freq_weight
    4) enforce unique label usage across categories
    """
    if not category_names or not analysis_rows:
        return 0, []

    rows_by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in analysis_rows:
        rows_by_category[str(row.get("dominant_category", ""))].append(row)

    used_labels: set[int] = set()
    pairs: list[dict[str, Any]] = []
    total_matched = 0

    for category in category_names:
        candidates = [
            r
            for r in rows_by_category.get(category, [])
            if int(r["label"]) not in used_labels
        ]

        filtered = [
            r
            for r in candidates
            if int(r.get("dominant_count", 0)) >= min_dominant_count
            and int(r.get("mapped_feature_count", 0)) >= min_mapped_feature_count
        ]

        # If everything gets filtered out, relax to dominant-category candidates.
        pool = filtered if filtered else candidates

        # Final fallback: any not-yet-used label.
        if not pool:
            pool = [r for r in analysis_rows if int(r["label"]) not in used_labels]

        if not pool:
            continue

        def rank_key(row: dict[str, Any]) -> tuple[float, int, int, float, int, int]:
            label = int(row["label"])
            matched = int(counts_by_label.get(label, Counter()).get(category, 0))
            return (
                float(row.get("avg_feature_freq_weight", 0.0)),
                int(row.get("dominant_count", 0)),
                matched,
                float(row.get("purity_percent", 0.0)),
                int(row.get("mapped_feature_count", 0)),
                -label,  # prefer smaller label id on ties
            )

        best_row = max(pool, key=rank_key)
        label = int(best_row["label"])
        matched_count = int(counts_by_label.get(label, Counter()).get(category, 0))
        used_labels.add(label)
        pairs.append(
            {
                "category": category,
                "label": label,
                "matched_count": matched_count,
            }
        )
        total_matched += matched_count

    pairs = sorted(pairs, key=lambda x: str(x["category"]))
    return total_matched, pairs


def add_purity_to_best_mapping(
    best_pairs: list[dict[str, Any]],
    analysis_rows: list[dict[str, Any]],
    category_totals: Counter[str],
) -> list[dict[str, Any]]:
    purity_by_label = {
        int(row["label"]): float(row["purity_percent"]) for row in analysis_rows
    }
    avg_feature_weight_by_label = {
        int(row["label"]): float(row.get("avg_feature_freq_weight", 0.0))
        for row in analysis_rows
    }
    out: list[dict[str, Any]] = []
    for pair in best_pairs:
        row = dict(pair)
        row["purity_percent"] = round(purity_by_label.get(int(pair["label"]), 0.0), 2)
        row["avg_feature_freq_weight"] = round(
            avg_feature_weight_by_label.get(int(pair["label"]), 0.0), 6
        )
        total = int(category_totals.get(str(pair["category"]), 0))
        matched = int(pair["matched_count"])
        row["recall_percent"] = round((100.0 * matched / total) if total else 0.0, 2)
        precision = float(row["purity_percent"])
        recall = float(row["recall_percent"])
        denom = precision + recall
        row["f1_percent"] = round((2.0 * precision * recall / denom) if denom > 0 else 0.0, 2)
        out.append(row)
    return out


def compute_summary_metrics(
    analysis_rows: list[dict[str, Any]],
    counts_by_label: dict[int, Counter[str]],
    category_names: list[str],
    category_totals: Counter[str],
) -> dict[str, Any]:
    n_labels = len(analysis_rows)
    total_animals_across_labels = sum(int(r["n_animals"]) for r in analysis_rows)
    total_dominant = sum(int(r["dominant_count"]) for r in analysis_rows)
    mean_purity = (
        sum(float(r["purity_percent"]) for r in analysis_rows) / n_labels if n_labels else 0.0
    )
    weighted_purity = (
        100.0 * total_dominant / total_animals_across_labels
        if total_animals_across_labels
        else 0.0
    )

    # Old distinct assignment logic (kept intentionally):
    # best_match_count, best_pairs = best_distinct_mapping(counts_by_label, category_names)
    # Old category-first logic (kept intentionally):
    # best_match_count, best_pairs = best_category_first_mapping_by_feature_weight(
    #     counts_by_label, category_names, analysis_rows
    # )
    # New logic: dominant-category candidates + weak-label filters + distinct labels.
    best_match_count, best_pairs = best_dominant_category_mapping_with_filters(
        counts_by_label,
        category_names,
        analysis_rows,
        min_dominant_count=5,
        min_mapped_feature_count=1,
    )
    best_pairs = add_purity_to_best_mapping(best_pairs, analysis_rows, category_totals)
    total_reference = sum(int(category_totals[c]) for c in category_names)
    best_match_accuracy = 100.0 * best_match_count / total_reference if total_reference else 0.0

    return {
        "n_labels": n_labels,
        "mean_purity_percent": round(mean_purity, 2),
        "weighted_purity_percent": round(weighted_purity, 2),
        "distinct_category_match_count": int(best_match_count),
        "distinct_category_match_accuracy_percent": round(best_match_accuracy, 2),
        "category_totals": {c: int(category_totals[c]) for c in category_names},
        "best_distinct_mapping": best_pairs,
    }


def parse_params(param_items: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in param_items:
        if "=" not in item:
            raise ValueError(f"Invalid --param '{item}'. Use key=value format.")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --param '{item}'. Key cannot be empty.")
        params[key] = value
    return params


def parse_bool_token(token: str) -> bool:
    t = token.strip().lower()
    if t in {"true", "1"}:
        return True
    if t in {"false", "0"}:
        return False
    raise ValueError(f"Invalid boolean token: '{token}' (expected true/false)")


def build_deleni_params_from_params(params: dict[str, str]) -> dict[str, Any]:
    keys = ["isColumnSplit", "max_col", "max_row", "prah"]
    if not any(k in params for k in keys):
        return {}

    out: dict[str, Any] = {}
    if "isColumnSplit" in params:
        out["isColumnSplit"] = parse_bool_token(params["isColumnSplit"])
    if "max_col" in params:
        out["max_col"] = int(params["max_col"])
    if "max_row" in params:
        out["max_row"] = int(params["max_row"])
    if "prah" in params:
        out["prah"] = round(float(params["prah"]), 6)
    return out


def format_summary_text(run_id: str, summary: dict[str, Any], deleni_params: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append(f"Run ID: {run_id}")
    if deleni_params:
        lines.append(f"Deleni params: {json.dumps(deleni_params)}")
    lines.append(f"Labels: {summary['n_labels']}")
    lines.append(f"Mean purity: {summary['mean_purity_percent']:.2f}%")
    lines.append(f"Weighted purity: {summary['weighted_purity_percent']:.2f}%")
    lines.append(
        "Best distinct 5-category match: "
        f"{summary['distinct_category_match_count']}/"
        f"{sum(summary['category_totals'].values())} "
        f"({summary['distinct_category_match_accuracy_percent']:.2f}%)"
    )
    lines.append("Category totals:")
    for category, total in summary["category_totals"].items():
        lines.append(f"{category}: {total}")
    lines.append("Best distinct mapping (category -> label):")
    for pair in summary["best_distinct_mapping"]:
        lines.append(
            f"{pair['category']} -> Label {pair['label']} "
            f"(matched={pair['matched_count']}, "
            f"purity={pair['purity_percent']:.2f}%, "
            f"recall={pair['recall_percent']:.2f}%)"
        )
    return "\n".join(lines) + "\n"


def write_leaderboard(leaderboard_path: Path, row: dict[str, Any]) -> None:
    leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    if leaderboard_path.exists():
        with leaderboard_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    row_str = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in row.items()}

    updated = False
    for i, existing in enumerate(rows):
        if existing.get("run_id") == row_str["run_id"]:
            # Preserve post-analysis metrics written by other scripts.
            if "overall_jaccard" in existing and "overall_jaccard" not in row_str:
                row_str["overall_jaccard"] = existing.get("overall_jaccard", "")
            rows[i] = row_str
            updated = True
            break
    if not updated:
        row_str.setdefault("overall_jaccard", "")
        rows.append(row_str)

    rows.sort(
        key=lambda r: (
            float(r.get("distinct_category_match_accuracy_percent", 0.0)),
            float(r.get("weighted_purity_percent", 0.0)),
        ),
        reverse=True,
    )

    fieldnames = [
        "run_id",
        "created_utc",
        "labels_file",
        "n_labels",
        "mean_purity_percent",
        "weighted_purity_percent",
        "distinct_category_match_count",
        "distinct_category_match_accuracy_percent",
        "params",
        "best_distinct_mapping",
        "overall_jaccard",
    ]
    normalized_rows: list[dict[str, str]] = []
    for existing in rows:
        normalized_rows.append({k: existing.get(k, "") for k in fieldnames})
    with leaderboard_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(
        description="Extract animals per label and evaluate category alignment."
    )
    parser.add_argument(
        "--animals",
        default="data/animals/animal_feature_matrix_dichotomized.csv",
        help="Path to animal_feature_matrix_dichotomized.csv",
    )
    parser.add_argument(
        "--labels",
        default=None,
        help="Path to label_membership_cells.csv. Optional if --run is provided.",
    )
    parser.add_argument(
        "--run",
        default=None,
        help=(
            "Run folder name under --runs-root (example: --run 3 => "
            "output/experiments/bmf/animals/category/all/3/label_membership_cells.csv)."
        ),
    )
    parser.add_argument(
        "--typicality",
        default="data/animals/typicality_ratings.csv",
        help="Path to typicality_ratings.csv",
    )
    parser.add_argument(
        "--feature-freq",
        default="data/animals/sum_features_freq_normalized.csv",
        help="Path to CSV with columns: features,freq,normalized_freq",
    )
    parser.add_argument(
        "--skip-label",
        type=int,
        default=None,
        help="Optional label id to skip (example: 1).",
    )
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help="Directory where experiment folders and leaderboard are stored.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for leaderboard row (defaults to run folder name).",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Experiment parameter in key=value form. Repeat for multiple values.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional override path for animals_by_label.txt",
    )
    parser.add_argument(
        "--analysis-out",
        default=None,
        help="Optional override path for label_category_analysis.txt",
    )
    parser.add_argument(
        "--analysis-csv",
        default=None,
        help="Optional override path for label_category_analysis.csv",
    )
    parser.add_argument(
        "--summary-out",
        default=None,
        help="Optional override path for summary.txt",
    )
    parser.add_argument(
        "--summary-json",
        default=None,
        help="Optional override path for summary.json",
    )
    args = parser.parse_args()

    animals_path = Path(args.animals)
    typicality_path = Path(args.typicality)
    feature_freq_path = Path(args.feature_freq)
    runs_root = Path(args.runs_root)
    params = parse_params(args.param)

    if args.labels:
        labels_path = Path(args.labels)
        run_dir = labels_path.parent
    else:
        if not args.run and not args.run_id:
            raise SystemExit("Provide either --run <name> or --labels <path>.")
        run_token = str(args.run) if args.run is not None else str(args.run_id)
        candidate_dirs = [runs_root / run_token, runs_root / f"run_{run_token}"]
        run_dir = next((d for d in candidate_dirs if d.exists()), candidate_dirs[0])
        labels_path = run_dir / "label_membership_cells.csv"

    run_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or (str(args.run) if args.run is not None else run_dir.name)
    if not run_id:
        run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")

    if not labels_path.exists():
        raise SystemExit(
            f"Missing labels file: {labels_path}. "
            "Put label_membership_cells.csv in that run folder or pass --labels."
        )
    if not feature_freq_path.exists():
        raise SystemExit(
            f"Missing feature frequency file: {feature_freq_path}. "
            "Generate it first via extract_sum_freq_normalized.py."
        )

    deleni_params = build_deleni_params_from_params(params)

    out_path = Path(args.out) if args.out else run_dir / "animals_by_label.txt"
    analysis_out_path = (
        Path(args.analysis_out) if args.analysis_out else run_dir / "label_category_analysis.txt"
    )
    analysis_csv_path = (
        Path(args.analysis_csv) if args.analysis_csv else run_dir / "label_category_analysis.csv"
    )
    summary_out_path = Path(args.summary_out) if args.summary_out else run_dir / "summary.txt"
    summary_json_path = Path(args.summary_json) if args.summary_json else run_dir / "summary.json"
    animals, feature_names = read_animals_and_features(animals_path)
    feature_weights = read_feature_weights(feature_freq_path)
    exemplar_to_category, category_totals = read_categories(typicality_path)
    rows_by_label, cols_by_label = read_label_membership(labels_path)
    label_animals = label_to_animals(rows_by_label, animals, args.skip_label)

    animals_text = format_animals_output(label_animals)
    analysis_text, analysis_rows, counts_by_label, category_names = analyze_label_categories(
        label_animals,
        exemplar_to_category,
        category_totals,
        cols_by_label,
        feature_names,
        feature_weights,
    )
    summary = compute_summary_metrics(
        analysis_rows, counts_by_label, category_names, category_totals
    )
    summary_payload: dict[str, Any] = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "animals": str(animals_path),
            "labels": str(labels_path),
            "typicality": str(typicality_path),
            "feature_freq": str(feature_freq_path),
            "skip_label": args.skip_label,
        },
        "params": params,
        "metrics": summary,
    }
    summary_text = format_summary_text(run_id, summary, deleni_params or None)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(animals_text, encoding="utf-8")
    analysis_out_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_out_path.write_text(analysis_text, encoding="utf-8")
    analysis_csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_analysis_csv(analysis_rows, analysis_csv_path)
    summary_out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_out_path.write_text(summary_text, encoding="utf-8")
    summary_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_json_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    leaderboard_path = runs_root / "leaderboard.csv"
    leaderboard_row = {
        "run_id": run_id,
        "created_utc": summary_payload["created_utc"],
        "labels_file": str(labels_path),
        "n_labels": summary["n_labels"],
        "mean_purity_percent": summary["mean_purity_percent"],
        "weighted_purity_percent": summary["weighted_purity_percent"],
        "distinct_category_match_count": summary["distinct_category_match_count"],
        "distinct_category_match_accuracy_percent": summary[
            "distinct_category_match_accuracy_percent"
        ],
        "params": params,
        "best_distinct_mapping": summary["best_distinct_mapping"],
    }
    write_leaderboard(leaderboard_path, leaderboard_row)

    print("Category Match Analysis")
    print("=======================")
    print(summary_text, end="")
    print(f"Saved: {out_path}")
    print(f"Saved: {analysis_out_path}")
    print(f"Saved: {analysis_csv_path}")
    print(f"Saved: {summary_out_path}")
    print(f"Saved: {summary_json_path}")
    print(f"Updated leaderboard: {leaderboard_path}")
    elapsed = time.perf_counter() - started
    append_processing_duration(run_dir, "extract_animals_by_label.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
