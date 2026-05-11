#!/usr/bin/env python3
"""Visualize run bundles with row labels, true categories, and bundle metrics."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RUNS_ROOT = "output/experiments/bmf/animals/category/all"


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def read_base_matrix(csv_path: Path) -> tuple[list[str], list[list[int]]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None or len(header) < 2:
            raise ValueError(f"Invalid matrix CSV: {csv_path}")
        names: list[str] = []
        matrix: list[list[int]] = []
        for row in reader:
            if not row:
                continue
            names.append(row[0].strip())
            matrix.append([int(v) for v in row[1:]])
    return names, matrix


def read_typicality_map(path: Path) -> dict[str, str]:
    exemplar_to_category: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
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
    return exemplar_to_category


def read_analysis_metrics(path: Path) -> dict[int, dict[str, str]]:
    metrics: dict[int, dict[str, str]] = {}
    if not path.exists():
        return metrics
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = int(row["label"])
            metrics[label] = {
                "dominant_category": row.get("dominant_category", "N/A"),
                "precision": row.get("purity_percent", "N/A"),
                "recall": row.get("dominant_recall_percent", "N/A"),
                "f1": row.get("dominant_f1_percent", "N/A"),
            }
    return metrics


def read_selected_labels_from_leaderboard(leaderboard_path: Path, run_id: str) -> set[int]:
    selected: set[int] = set()
    if not leaderboard_path.exists():
        return selected

    with leaderboard_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if str(row.get("run_id", "")).strip() != str(run_id).strip():
                continue
            raw = row.get("best_distinct_mapping", "")
            if not raw:
                return selected
            try:
                pairs = json.loads(raw)
            except Exception:
                return selected
            for pair in pairs:
                try:
                    selected.add(int(pair.get("label")))
                except Exception:
                    continue
            return selected
    return selected


def read_label_membership(path: Path) -> list[dict[str, int]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            {
                "label": int(r["label"]),
                "row_new": int(r["row_new"]),
                "col_new": int(r["col_new"]),
                "row_orig": int(r["row_orig"]),
                "col_orig": int(r["col_orig"]),
            }
            for r in reader
        ]


def build_row_perm(records: list[dict[str, int]], n_rows: int) -> list[int]:
    by_new: dict[int, int] = {}
    for r in records:
        rn = r["row_new"]
        ro = r["row_orig"]
        if rn in by_new and by_new[rn] != ro:
            raise ValueError(f"Inconsistent row mapping for row_new={rn}: {by_new[rn]} vs {ro}")
        by_new[rn] = ro
    missing = [i for i in range(1, n_rows + 1) if i not in by_new]
    if missing:
        raise ValueError(f"Missing row mappings for row_new: {missing[:10]}")
    return [by_new[i] for i in range(1, n_rows + 1)]


def build_col_perm(records: list[dict[str, int]], n_cols: int) -> tuple[list[int], int]:
    by_new: dict[int, int] = {}
    for r in records:
        cn = r["col_new"]
        co = r["col_orig"]
        if cn in by_new and by_new[cn] != co:
            raise ValueError(f"Inconsistent col mapping for col_new={cn}: {by_new[cn]} vs {co}")
        by_new[cn] = co

    used_orig = set(by_new.values())
    missing_new = [i for i in range(1, n_cols + 1) if i not in by_new]
    missing_orig = [i for i in range(1, n_cols + 1) if i not in used_orig]

    # Deterministic fallback for any unobserved columns.
    for cn, co in zip(missing_new, missing_orig):
        by_new[cn] = co

    perm = [by_new[i] for i in range(1, n_cols + 1)]
    inferred_count = len(missing_new)
    return perm, inferred_count


def reorder_matrix(base: list[list[int]], row_perm: list[int], col_perm: list[int]) -> list[list[int]]:
    return [[base[r - 1][c - 1] for c in col_perm] for r in row_perm]


def label_boxes(
    records: list[dict[str, int]], background_label: int = 1
) -> dict[int, tuple[int, int, int, int]]:
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for r in records:
        label = r["label"]
        if label == background_label:
            continue
        rn = r["row_new"]
        cn = r["col_new"]
        if label not in boxes:
            boxes[label] = (rn, cn, rn, cn)
        else:
            rmin, cmin, rmax, cmax = boxes[label]
            boxes[label] = (min(rmin, rn), min(cmin, cn), max(rmax, rn), max(cmax, cn))
    return boxes


def fmt_pct(value: str) -> str:
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return "N/A"


def median_f1_selected_label(
    selected_labels: set[int], metrics_by_label: dict[int, dict[str, str]]
) -> tuple[int | None, float | None]:
    """Return selected label closest to median F1 and the median F1 value."""
    candidates: list[tuple[int, float]] = []
    for label in sorted(selected_labels):
        metrics = metrics_by_label.get(label, {})
        try:
            f1 = float(metrics.get("f1", ""))
        except Exception:
            continue
        candidates.append((label, f1))

    if not candidates:
        return None, None

    median_f1 = float(statistics.median([f1 for _, f1 in candidates]))
    # Closest to median; tie-break by lower label id for deterministic output.
    best_label, _ = min(candidates, key=lambda x: (abs(x[1] - median_f1), x[0]))
    return best_label, median_f1


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


def write_svg(
    matrix: list[list[int]],
    boxes: dict[int, tuple[int, int, int, int]],
    row_objects: list[str],
    row_categories: list[str],
    metrics_by_label: dict[int, dict[str, str]],
    selected_labels: set[int],
    median_label: int | None,
    out_path: Path,
    cell_size: int = 4,
    pad: int = 8,
) -> None:
    n_rows = len(matrix)
    n_cols = len(matrix[0]) if matrix else 0

    row_font = max(4, cell_size)  # all rows shown; tiny but aligned
    panel_font = max(11, row_font + 6)
    panel_line_h = int(panel_font * 1.35)

    max_obj_len = max((len(x) for x in row_objects), default=10)
    max_cat_len = max((len(x) for x in row_categories), default=8)
    # Simple text-width approximation in pixels.
    left_w = int(max_obj_len * row_font * 0.62) + 40
    right_w = int(max_cat_len * row_font * 0.62) + 30
    panel_w = 520

    matrix_x = pad + left_w
    matrix_y = pad
    category_x = matrix_x + n_cols * cell_size + 12
    panel_x = category_x + right_w + 18
    panel_y = pad + panel_font

    w = panel_x + panel_w + pad
    # Panel needs space for: title + labels + blank line + 2 legend lines.
    h = max(matrix_y + n_rows * cell_size + pad, panel_y + (len(boxes) + 5) * panel_line_h + pad)

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    lines.append('<rect x="0" y="0" width="100%" height="100%" fill="#202124"/>')

    # Matrix cells.
    for i, row in enumerate(matrix):
        y = matrix_y + i * cell_size
        for j, v in enumerate(row):
            x = matrix_x + j * cell_size
            color = "#000000" if v == 1 else "#e6e6e6"
            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}"/>'
            )

    # Row labels: object on left, true category on right.
    baseline_shift = row_font * 0.35
    for i in range(n_rows):
        y_text = matrix_y + i * cell_size + (cell_size / 2.0) + baseline_shift
        obj = xml_escape(row_objects[i])
        cat = xml_escape(row_categories[i])
        lines.append(
            f'<text x="{matrix_x - 8}" y="{y_text:.2f}" '
            f'font-size="{row_font}" font-family="monospace" fill="#f2f2f2" '
            'text-anchor="end">'
            f"{obj}</text>"
        )
        lines.append(
            f'<text x="{category_x}" y="{y_text:.2f}" '
            f'font-size="{row_font}" font-family="monospace" fill="#d7d7d7" '
            'text-anchor="start">'
            f"{cat}</text>"
        )

    # Red rectangles for non-background bundles + top-left label marker.
    rect_label_font = max(8, cell_size * 2)
    for label in sorted(boxes):
        rmin, cmin, rmax, cmax = boxes[label]
        x = matrix_x + (cmin - 1) * cell_size
        y = matrix_y + (rmin - 1) * cell_size
        bw = (cmax - cmin + 1) * cell_size
        bh = (rmax - rmin + 1) * cell_size
        lines.append(
            f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" '
            'fill="none" stroke="#ff0000" stroke-width="1"/>'
        )
        label_text = f"L{label}"
        label_x = x + 2
        label_y = y + rect_label_font
        if label == median_label:
            label_color = "#ff9900"  # Median selected label.
        elif label in selected_labels:
            label_color = "#00cc44"  # Selected labels from best_distinct_mapping.
        else:
            label_color = "#ff0000"  # Non-selected labels.
        lines.append(
            f'<text x="{label_x}" y="{label_y}" font-size="{rect_label_font}" '
            f'font-family="monospace" fill="{label_color}" text-anchor="start">'
            f"{xml_escape(label_text)}</text>"
        )

    # Bundle metrics panel.
    lines.append(
        f'<text x="{panel_x}" y="{panel_y}" font-size="{panel_font}" '
        'font-family="monospace" fill="#ffffff" text-anchor="start">'
        "Bundle Metrics (precision=purity, recall=dominant recall, f1=dominant f1)</text>"
    )
    y_line = panel_y + panel_line_h
    for label in sorted(boxes):
        m = metrics_by_label.get(label, {})
        dom = xml_escape(m.get("dominant_category", "N/A"))
        prec = fmt_pct(m.get("precision", "N/A"))
        rec = fmt_pct(m.get("recall", "N/A"))
        f1 = fmt_pct(m.get("f1", "N/A"))
        marker = "** " if label == median_label else "* " if label in selected_labels else "  "
        text = f"{marker}Label {label} ({dom}): precision={prec} recall={rec} f1={f1}"
        lines.append(
            f'<text x="{panel_x}" y="{y_line}" font-size="{panel_font}" '
            'font-family="monospace" fill="#ffcccc" text-anchor="start">'
            f"{xml_escape(text)}</text>"
        )
        y_line += panel_line_h

    # Legend after all labels, with one blank line gap.
    y_line += panel_line_h
    lines.append(
        f'<text x="{panel_x}" y="{y_line}" font-size="{panel_font}" '
        'font-family="monospace" fill="#ffcccc" text-anchor="start">'
        "* = selected bundle</text>"
    )
    y_line += panel_line_h
    lines.append(
        f'<text x="{panel_x}" y="{y_line}" font-size="{panel_font}" '
        'font-family="monospace" fill="#ffcccc" text-anchor="start">'
        "** = selected bundle with median F1</text>"
    )

    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description="Visualize bundle rectangles for a run.")
    parser.add_argument("--run", default=None, help="Run id, e.g. 7")
    parser.add_argument(
        "--run-dir",
        default=None,
        help=(
            "Optional explicit run directory path, e.g. "
            "output/experiments/bmf/animals/category/all/preferred/8"
        ),
    )
    parser.add_argument(
        "--base-matrix",
        default="data/animals/animal_feature_matrix_dichotomized.csv",
        help="Path to base matrix CSV",
    )
    parser.add_argument(
        "--typicality",
        default="data/animals/typicality_ratings.csv",
        help="Path to typicality_ratings.csv",
    )
    parser.add_argument(
        "--analysis-csv",
        default=None,
        help="Optional label_category_analysis.csv path (defaults to run folder file)",
    )
    parser.add_argument(
        "--leaderboard",
        default=None,
        help="Optional leaderboard.csv path (defaults to <runs-root>/leaderboard.csv)",
    )
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help="Runs root directory",
    )
    parser.add_argument("--cell-size", type=int, default=4, help="SVG cell size in pixels")
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Optional SVG output path "
            "(default: output/experiments/bmf/animals/category/all/<run>/bundle_overlay.svg)"
        ),
    )
    parser.add_argument(
        "--background-label",
        type=int,
        default=1,
        help="Label id treated as background (no rectangle). Default: 1",
    )
    args = parser.parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir)
        run_id = str(args.run) if args.run is not None else run_dir.name
    else:
        if args.run is None:
            raise SystemExit("Provide --run (or use --run-dir).")
        run_id = str(args.run)
        run_dir = Path(args.runs_root) / run_id

    labels_path = run_dir / "label_membership_cells.csv"
    analysis_path = Path(args.analysis_csv) if args.analysis_csv else run_dir / "label_category_analysis.csv"
    if args.leaderboard:
        leaderboard_path = Path(args.leaderboard)
    else:
        # Preferred-run convenience:
        # .../<branch>/preferred/<run_id> -> leaderboard at .../<branch>/leaderboard.csv
        if run_dir.parent.name == "preferred":
            leaderboard_path = run_dir.parent.parent / "leaderboard.csv"
        else:
            leaderboard_path = Path(args.runs_root) / "leaderboard.csv"
    out_path = Path(args.out) if args.out else run_dir / "bundle_overlay.svg"

    if not labels_path.exists():
        raise SystemExit(f"Missing labels file: {labels_path}")

    object_names, base = read_base_matrix(Path(args.base_matrix))
    exemplar_to_category = read_typicality_map(Path(args.typicality))
    metrics_by_label = read_analysis_metrics(analysis_path)
    selected_labels = read_selected_labels_from_leaderboard(leaderboard_path, run_id)
    median_label, median_f1 = median_f1_selected_label(selected_labels, metrics_by_label)
    records = read_label_membership(labels_path)
    n_rows = len(base)
    n_cols = len(base[0]) if base else 0

    row_perm = build_row_perm(records, n_rows)
    col_perm, inferred_count = build_col_perm(records, n_cols)
    matrix = reorder_matrix(base, row_perm, col_perm)
    boxes = label_boxes(records, background_label=args.background_label)

    row_objects = [object_names[orig - 1] for orig in row_perm]
    row_categories = [exemplar_to_category.get(name.strip(), "unknown") for name in row_objects]

    write_svg(
        matrix,
        boxes,
        row_objects,
        row_categories,
        metrics_by_label,
        selected_labels,
        median_label,
        out_path,
        cell_size=args.cell_size,
    )

    print(f"Run: {run_id}")
    print(f"Base matrix: {n_rows}x{n_cols}")
    print(f"Background label: {args.background_label}")
    print(f"Labels used for boxes (excluding background): {len(boxes)}")
    print(f"Rows annotated: {len(row_objects)}")
    print(f"Columns inferred due to missing mappings: {inferred_count}")
    print(f"Metrics source: {analysis_path}")
    print(f"Selected labels source: {leaderboard_path}")
    print(f"Selected labels in best_distinct_mapping: {sorted(selected_labels)}")
    if median_label is not None and median_f1 is not None:
        print(f"Median-F1 selected label: {median_label} (median_f1={median_f1:.2f}%)")
    else:
        print("Median-F1 selected label: N/A")
    print(f"Saved SVG: {out_path}")
    elapsed = time.perf_counter() - started
    append_processing_duration(run_dir, "visualize_bundles.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")


if __name__ == "__main__":
    main()
