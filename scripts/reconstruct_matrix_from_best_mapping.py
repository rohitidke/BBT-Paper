#!/usr/bin/env python3
"""Rebuild a binary matrix from best_distinct_mapping labels for a given run."""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RUNS_ROOT = "output/experiments/bmf/animals/category/all"


def resolve_run_dir(runs_root: Path, run_id: str) -> Path:
    direct = runs_root / run_id
    if direct.exists():
        return direct
    alt = runs_root / f"run_{run_id}"
    if alt.exists():
        return alt
    return direct


def read_best_mapping(leaderboard_path: Path, run_id: str) -> list[dict]:
    with leaderboard_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("run_id") == run_id:
                raw = row.get("best_distinct_mapping", "").strip()
                if not raw:
                    raise ValueError(f"best_distinct_mapping is empty for run '{run_id}'.")
                return json.loads(raw)
    raise ValueError(f"Run '{run_id}' not found in {leaderboard_path}.")


def collect_cells_by_labels(
    label_csv_path: Path,
    labels: set[int] | None,
    row_key: str,
    col_key: str,
    excluded_labels: set[int] | None = None,
) -> tuple[list[tuple[int, int]], set[int]]:
    cells: list[tuple[int, int]] = []
    seen_labels: set[int] = set()
    excluded = excluded_labels or set()
    with label_csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = int(row["label"])
            seen_labels.add(label)
            if label in excluded:
                continue
            if labels is None or label in labels:
                r = int(row[row_key])
                c = int(row[col_key])
                cells.append((r, c))
    return cells, seen_labels


def build_binary_matrix(rows: int, cols: int, cells: list[tuple[int, int]]) -> tuple[list[list[int]], int]:
    matrix = [[0 for _ in range(cols)] for _ in range(rows)]
    out_of_bounds = 0
    for r, c in cells:
        rr = r - 1
        cc = c - 1
        if 0 <= rr < rows and 0 <= cc < cols:
            matrix[rr][cc] = 1
        else:
            out_of_bounds += 1
    return matrix, out_of_bounds


def write_matrix_csv(matrix: list[list[int]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(matrix)


def print_matrix(matrix: list[list[int]]) -> None:
    for row in matrix:
        print(" ".join(str(v) for v in row))


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(
        description="Build 129x225 binary matrix using best_distinct_mapping labels for a run."
    )
    parser.add_argument("run_id", help="Run id, e.g. 6")
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help=f"Experiments root directory (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--leaderboard",
        default=None,
        help="Path to leaderboard.csv (default: <runs-root>/leaderboard.csv)",
    )
    parser.add_argument("--rows", type=int, default=129, help="Output matrix row count")
    parser.add_argument("--cols", type=int, default=225, help="Output matrix column count")
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output CSV path (default: <run_dir>/reconstructed_matrix.csv)",
    )
    parser.add_argument(
        "--all-labels",
        action="store_true",
        help="Use all labels from label_membership_cells.csv (ignore best_distinct_mapping).",
    )
    parser.add_argument(
        "--background-label",
        type=int,
        default=1,
        help="Background label to exclude when using --all-labels (default: 1).",
    )
    args = parser.parse_args()

    run_id = str(args.run_id)
    runs_root = Path(args.runs_root)
    run_dir = resolve_run_dir(runs_root, run_id)
    labels_csv = run_dir / "label_membership_cells.csv"
    leaderboard_path = (
        Path(args.leaderboard) if args.leaderboard else runs_root / "leaderboard.csv"
    )

    if not labels_csv.exists():
        raise SystemExit(f"Missing labels file: {labels_csv}")
    mapping: list[dict] = []
    by_category: dict[str, int] = {}
    labels: set[int] | None = None

    if not args.all_labels:
        if not leaderboard_path.exists():
            raise SystemExit(f"Missing leaderboard file: {leaderboard_path}")
        mapping = read_best_mapping(leaderboard_path, run_id)
        labels = {int(item["label"]) for item in mapping}
        by_category = {item["category"]: int(item["label"]) for item in mapping}

    # Original-coordinate reconstruction.
    exclude_in_all = {int(args.background_label)} if args.all_labels else set()
    cells_orig, seen_labels = collect_cells_by_labels(
        labels_csv,
        labels,
        row_key="row_orig",
        col_key="col_orig",
        excluded_labels=exclude_in_all,
    )
    matrix_orig, out_of_bounds_orig = build_binary_matrix(args.rows, args.cols, cells_orig)

    # Reordered-coordinate reconstruction.
    cells_new, _ = collect_cells_by_labels(
        labels_csv,
        labels,
        row_key="row_new",
        col_key="col_new",
        excluded_labels=exclude_in_all,
    )
    matrix_new, out_of_bounds_new = build_binary_matrix(args.rows, args.cols, cells_new)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = (
            run_dir / "reconstructed_matrix_all_labels.csv"
            if args.all_labels
            else run_dir / "reconstructed_matrix.csv"
        )
    out_reordered_path = (
        run_dir / "reconstructed_matrix_reordered_all_labels.csv"
        if args.all_labels
        else run_dir / "reconstructed_matrix_reordered.csv"
    )
    write_matrix_csv(matrix_orig, out_path)
    write_matrix_csv(matrix_new, out_reordered_path)

    used_labels = sorted(seen_labels) if labels is None else sorted(labels)

    print(f"Run: {run_id}")
    if args.all_labels:
        print("Mode: all labels")
        print(f"Excluded background label: {args.background_label}")
    else:
        print("Mode: best_distinct_mapping labels")
        print(f"Category -> Label mapping: {by_category}")
    print(f"Used labels: {used_labels}")
    print(f"Collected cells (orig): {len(cells_orig)}")
    print(f"Out-of-bounds cells skipped (orig): {out_of_bounds_orig}")
    print(f"Collected cells (reordered): {len(cells_new)}")
    print(f"Out-of-bounds cells skipped (reordered): {out_of_bounds_new}")
    print(f"Saved matrix CSV (orig): {out_path}")
    print(f"Saved matrix CSV (reordered): {out_reordered_path}")
    elapsed = time.perf_counter() - started
    append_processing_duration(run_dir, "reconstruct_matrix_from_best_mapping.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")

if __name__ == "__main__":
    main()
