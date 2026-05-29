#!/usr/bin/env python3
"""Compute block-wise density for a binary matrix by splitting it into a grid."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a binary matrix CSV, split it into a grid (default 3x3), and "
            "compute density for each block as number_of_ones / number_of_cells."
        )
    )
    parser.add_argument(
        "input_csv",
        help="Path to the input matrix CSV.",
    )
    parser.add_argument(
        "--parts",
        type=int,
        default=3,
        help="Number of row-parts and column-parts to use (default: 3).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Optional output CSV path. Defaults to "
            "<input_dir>/<input_stem>_grid_density_<parts>x<parts>.csv"
        ),
    )
    return parser.parse_args()


def split_indices(length: int, parts: int) -> list[tuple[int, int]]:
    base = length // parts
    remainder = length % parts
    ranges: list[tuple[int, int]] = []
    start = 0
    for idx in range(parts):
        size = base + (1 if idx < remainder else 0)
        end = start + size
        ranges.append((start, end))
        start = end
    return ranges


def load_numeric_matrix(path: Path) -> list[list[int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Empty CSV: {path}")

    data_rows = rows

    # Drop header row if it contains any non-numeric cell.
    if any(not cell.strip().isdigit() for cell in rows[0]):
        data_rows = rows[1:]

    if not data_rows:
        raise ValueError(f"No matrix rows found in {path}")

    matrix: list[list[int]] = []
    for row in data_rows:
        if not row:
            continue

        numeric_cells = row
        # Drop first column if it is a label column.
        if row and not row[0].strip().isdigit():
            numeric_cells = row[1:]

        if not numeric_cells:
            continue

        matrix_row: list[int] = []
        for value in numeric_cells:
            text = value.strip()
            if text == "":
                matrix_row.append(0)
            else:
                matrix_row.append(1 if float(text) > 0 else 0)
        matrix.append(matrix_row)

    if not matrix:
        raise ValueError(f"No numeric matrix values found in {path}")

    width = len(matrix[0])
    for idx, row in enumerate(matrix, start=1):
        if len(row) != width:
            raise ValueError(f"Non-rectangular matrix at data row {idx} in {path}")
    return matrix


def compute_block_density(
    matrix: list[list[int]],
    row_ranges: list[tuple[int, int]],
    col_ranges: list[tuple[int, int]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for row_block, (row_start, row_end) in enumerate(row_ranges, start=1):
        for col_block, (col_start, col_end) in enumerate(col_ranges, start=1):
            ones = 0
            total = 0
            for row in matrix[row_start:row_end]:
                for value in row[col_start:col_end]:
                    total += 1
                    ones += int(value)
            density = (ones / total) if total else 0.0
            results.append(
                {
                    "row_block": row_block,
                    "col_block": col_block,
                    "row_start_1based": row_start + 1,
                    "row_end_1based": row_end,
                    "col_start_1based": col_start + 1,
                    "col_end_1based": col_end,
                    "ones": ones,
                    "total_cells": total,
                    "fraction": f"{ones}/{total}",
                    "density": f"{density:.6f}",
                }
            )
    return results


def default_output_path(input_csv: Path, parts: int) -> Path:
    return input_csv.with_name(f"{input_csv.stem}_grid_density_{parts}x{parts}.csv")


def write_results(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "row_block",
        "col_block",
        "row_start_1based",
        "row_end_1based",
        "col_start_1based",
        "col_end_1based",
        "ones",
        "total_cells",
        "fraction",
        "density",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_fraction_grid(results: list[dict[str, object]], parts: int) -> None:
    print("Block densities (ones/total_cells):")
    for row_block in range(1, parts + 1):
        fractions = [
            str(item["fraction"])
            for item in results
            if int(item["row_block"]) == row_block
        ]
        print("  " + "  ".join(fractions))


def main() -> None:
    args = parse_args()
    if args.parts <= 0:
        raise ValueError("--parts must be a positive integer.")

    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    matrix = load_numeric_matrix(input_csv)
    n_rows = len(matrix)
    n_cols = len(matrix[0]) if matrix else 0

    if args.parts > n_rows or args.parts > n_cols:
        raise ValueError(
            f"Cannot split matrix of shape {n_rows}x{n_cols} into "
            f"{args.parts}x{args.parts} blocks."
        )

    row_ranges = split_indices(n_rows, args.parts)
    col_ranges = split_indices(n_cols, args.parts)
    results = compute_block_density(matrix, row_ranges, col_ranges)

    output_path = Path(args.out) if args.out else default_output_path(input_csv, args.parts)
    write_results(output_path, results)

    print(f"Matrix shape: {n_rows} x {n_cols}")
    print(f"Grid: {args.parts} x {args.parts}")
    print_fraction_grid(results, args.parts)
    print(f"Wrote block densities: {output_path}")


if __name__ == "__main__":
    main()
