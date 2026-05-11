#!/usr/bin/env python3
"""Visualize reordered original + two reconstructed reordered matrices in one SVG."""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_RUNS_ROOT = "output/experiments/bmf/animals/exemplar/all/preferred"


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


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
            matrix.append([1 if int(v) > 0 else 0 for v in row[1:]])
    return names, matrix


def read_binary_matrix_no_header(path: Path) -> list[list[int]]:
    matrix: list[list[int]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            vals = [1 if int(float(v)) > 0 else 0 for v in row]
            matrix.append(vals)
    if not matrix:
        raise ValueError(f"Empty matrix file: {path}")
    n_cols = len(matrix[0])
    for i, row in enumerate(matrix, start=1):
        if len(row) != n_cols:
            raise ValueError(f"Non-rectangular matrix at row {i} in {path}")
    return matrix


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


def build_col_perm(records: list[dict[str, int]], n_cols: int) -> list[int]:
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
    for cn, co in zip(missing_new, missing_orig):
        by_new[cn] = co

    return [by_new[i] for i in range(1, n_cols + 1)]


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


def draw_matrix(
    lines: list[str],
    matrix: list[list[int]],
    x0: int,
    y0: int,
    cell_size: int,
) -> None:
    for i, row in enumerate(matrix):
        y = y0 + i * cell_size
        for j, v in enumerate(row):
            x = x0 + j * cell_size
            color = "#000000" if v == 1 else "#e6e6e6"
            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}"/>'
            )


def write_svg(
    original_reordered: list[list[int]],
    reconstructed_all_labels_reordered: list[list[int]],
    reconstructed_selected_reordered: list[list[int]],
    boxes: dict[int, tuple[int, int, int, int]],
    out_path: Path,
    cell_size: int = 3,
) -> None:
    n_rows = len(original_reordered)
    n_cols = len(original_reordered[0]) if original_reordered else 0

    for name, m in [
        ("reconstructed_all_labels_reordered", reconstructed_all_labels_reordered),
        ("reconstructed_selected_reordered", reconstructed_selected_reordered),
    ]:
        if len(m) != n_rows or (len(m[0]) if m else 0) != n_cols:
            raise ValueError(
                f"Shape mismatch for {name}: got {len(m)}x{(len(m[0]) if m else 0)} "
                f"expected {n_rows}x{n_cols}"
            )

    pad = 12
    title_h = 18
    panel_gap = 18
    matrix_h = n_rows * cell_size
    matrix_w = n_cols * cell_size
    x0 = pad

    y1 = pad + title_h
    y2 = y1 + matrix_h + panel_gap + title_h
    y3 = y2 + matrix_h + panel_gap + title_h

    w = x0 + matrix_w + pad
    h = y3 + matrix_h + pad

    lines: list[str] = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    lines.append('<rect x="0" y="0" width="100%" height="100%" fill="#202124"/>')

    # Panel titles.
    lines.append(
        f'<text x="{x0}" y="{y1 - 5}" font-size="12" font-family="monospace" fill="#ffffff">'
        f"{xml_escape('1) Reordered original matrix')}</text>"
    )
    lines.append(
        f'<text x="{x0}" y="{y2 - 5}" font-size="12" font-family="monospace" fill="#ffffff">'
        f"{xml_escape('2) Reconstructed reordered (all labels)')}</text>"
    )
    lines.append(
        f'<text x="{x0}" y="{y3 - 5}" font-size="12" font-family="monospace" fill="#ffffff">'
        f"{xml_escape('3) Reconstructed reordered (selected labels)')}</text>"
    )

    draw_matrix(lines, original_reordered, x0, y1, cell_size)
    draw_matrix(lines, reconstructed_all_labels_reordered, x0, y2, cell_size)
    draw_matrix(lines, reconstructed_selected_reordered, x0, y3, cell_size)

    # Draw red bundle rectangles on the first panel only.
    for label in sorted(boxes):
        rmin, cmin, rmax, cmax = boxes[label]
        x = x0 + (cmin - 1) * cell_size
        y = y1 + (rmin - 1) * cell_size
        bw = (cmax - cmin + 1) * cell_size
        bh = (rmax - rmin + 1) * cell_size
        lines.append(
            f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" '
            'fill="none" stroke="#ff0000" stroke-width="1"/>'
        )

    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def resolve_run_dir(runs_root: Path, run_id: str) -> Path:
    direct = runs_root / run_id
    if direct.exists():
        return direct
    alt = runs_root / f"run_{run_id}"
    if alt.exists():
        return alt
    return direct


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser(
        description="Visualize original reordered + reconstructed reordered matrices in one SVG."
    )
    parser.add_argument("--run", default=None, help="Run id, e.g. 8")
    parser.add_argument(
        "--run-dir",
        default=None,
        help="Optional explicit run directory, e.g. output/.../preferred/user_based",
    )
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help=f"Runs root directory (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--base-matrix",
        default="data/animals/animal_exemplar_feature_matrix_dichotomized.csv",
        help="Path to base matrix CSV with first column as object names",
    )
    parser.add_argument(
        "--labels-csv",
        default=None,
        help="Optional label_membership_cells.csv path (default: <run_dir>/label_membership_cells.csv)",
    )
    parser.add_argument(
        "--reconstructed-all",
        default=None,
        help=(
            "Optional reordered all-labels matrix CSV path "
            "(default: <run_dir>/reconstructed_matrix_reordered_all_labels.csv)"
        ),
    )
    parser.add_argument(
        "--reconstructed-selected",
        default=None,
        help=(
            "Optional reordered selected-labels matrix CSV path "
            "(default: <run_dir>/reconstructed_matrix_reordered.csv)"
        ),
    )
    parser.add_argument(
        "--background-label",
        type=int,
        default=1,
        help="Label id treated as background for red rectangles (default: 1)",
    )
    parser.add_argument("--cell-size", type=int, default=3, help="Cell size in pixels")
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Optional output SVG path "
            "(default: <run_dir>/reconstructed_matrices_overlay.svg)"
        ),
    )
    args = parser.parse_args()

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        if args.run is None:
            raise SystemExit("Provide --run (or use --run-dir).")
        run_dir = resolve_run_dir(Path(args.runs_root), str(args.run))

    labels_path = Path(args.labels_csv) if args.labels_csv else run_dir / "label_membership_cells.csv"
    all_path = (
        Path(args.reconstructed_all)
        if args.reconstructed_all
        else run_dir / "reconstructed_matrix_reordered_all_labels.csv"
    )
    selected_path = (
        Path(args.reconstructed_selected)
        if args.reconstructed_selected
        else run_dir / "reconstructed_matrix_reordered.csv"
    )
    out_path = Path(args.out) if args.out else run_dir / "reconstructed_matrices_overlay.svg"

    if not labels_path.exists():
        raise SystemExit(f"Missing labels file: {labels_path}")
    if not all_path.exists():
        raise SystemExit(f"Missing all-labels reconstructed matrix: {all_path}")
    if not selected_path.exists():
        raise SystemExit(f"Missing selected-labels reconstructed matrix: {selected_path}")

    _, base = read_base_matrix(Path(args.base_matrix))
    records = read_label_membership(labels_path)
    n_rows = len(base)
    n_cols = len(base[0]) if base else 0
    row_perm = build_row_perm(records, n_rows)
    col_perm = build_col_perm(records, n_cols)
    original_reordered = reorder_matrix(base, row_perm, col_perm)
    boxes = label_boxes(records, background_label=args.background_label)

    reconstructed_all = read_binary_matrix_no_header(all_path)
    reconstructed_selected = read_binary_matrix_no_header(selected_path)

    write_svg(
        original_reordered,
        reconstructed_all,
        reconstructed_selected,
        boxes,
        out_path,
        cell_size=args.cell_size,
    )

    print(f"Run dir: {run_dir}")
    print(f"Base matrix shape (reordered): {n_rows}x{n_cols}")
    print(f"All-labels matrix: {all_path}")
    print(f"Selected-labels matrix: {selected_path}")
    print(f"Saved SVG: {out_path}")
    elapsed = time.perf_counter() - started
    append_processing_duration(run_dir, "visualize_reconstructed_matrices.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")


if __name__ == "__main__":
    main()

