#!/usr/bin/env python3
"""Create ranking tables and Matplotlib scatter plots from typicality/Jaccard data."""

from __future__ import annotations

import argparse
import csv
import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read a typicality_similarity_enriched.csv file and write a CSV that "
            "compares descending Jaccard and typicality rankings side by side for "
            "each category. Also writes a single Matplotlib figure with one scatter "
            "plot per category."
        )
    )
    parser.add_argument(
        "input_csv",
        help="Path to typicality_similarity_enriched.csv",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Optional output CSV path. Defaults to "
            "<input_dir>/<input_stem>_jaccard_typicality_rankings.csv"
        ),
    )
    parser.add_argument(
        "--plot-out",
        default=None,
        help=(
            "Optional output plot path. Defaults to "
            "<input_dir>/<input_stem>_jaccard_typicality_scatter_by_category.svg"
        ),
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip scatter plot generation.",
    )
    parser.add_argument(
        "--category-column",
        default="category",
        help="Category column name (default: category)",
    )
    parser.add_argument(
        "--item-column",
        default="exemplar",
        help="Item/exemplar column name (default: exemplar)",
    )
    parser.add_argument(
        "--jaccard-column",
        default="rowwise_similarity",
        help="Jaccard column name (default: rowwise_similarity)",
    )
    parser.add_argument(
        "--typicality-column",
        default="typicality_rating",
        help="Typicality column name (default: typicality_rating)",
    )
    return parser.parse_args()


def to_float(value: str) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def validate_columns(fieldnames: list[str] | None, required: set[str]) -> None:
    if fieldnames is None:
        raise ValueError("Input CSV does not have a header row.")
    missing = sorted(required - set(fieldnames))
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {missing}")


def load_rows(
    csv_path: Path,
    category_column: str,
    item_column: str,
    jaccard_column: str,
    typicality_column: str,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        validate_columns(
            reader.fieldnames,
            {category_column, item_column, jaccard_column, typicality_column},
        )
        for row in reader:
            category = str(row[category_column]).strip()
            exemplar = str(row[item_column]).strip()
            grouped[category].append(
                {
                    "category": category,
                    "item": exemplar,
                    "jaccard": to_float(row[jaccard_column]),
                    "typicality": to_float(row[typicality_column]),
                }
            )
    return grouped


def descending_sort_key(row: dict[str, Any], metric: str) -> tuple[bool, float, str]:
    value = row[metric]
    return (value is None, -(value if value is not None else 0.0), row["item"].lower())


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def build_output_rows(grouped_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for category in sorted(grouped_rows):
        rows = grouped_rows[category]
        jaccard_ranked = sorted(rows, key=lambda row: descending_sort_key(row, "jaccard"))
        typicality_ranked = sorted(
            rows,
            key=lambda row: descending_sort_key(row, "typicality"),
        )

        for index in range(max(len(jaccard_ranked), len(typicality_ranked))):
            jaccard_row = jaccard_ranked[index] if index < len(jaccard_ranked) else None
            typicality_row = (
                typicality_ranked[index] if index < len(typicality_ranked) else None
            )
            output_rows.append(
                {
                    "category": category,
                    "jaccard_rank": str(index + 1) if jaccard_row else "",
                    "jaccard_exemplar": jaccard_row["item"] if jaccard_row else "",
                    "jaccard_index": (
                        format_number(jaccard_row["jaccard"]) if jaccard_row else ""
                    ),
                    "typicality_rank": str(index + 1) if typicality_row else "",
                    "typicality_exemplar": (
                        typicality_row["item"] if typicality_row else ""
                    ),
                    "typicality_rating": (
                        format_number(typicality_row["typicality"])
                        if typicality_row
                        else ""
                    ),
                }
            )
    return output_rows


def write_output(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "jaccard_rank",
        "jaccard_exemplar",
        "jaccard_index",
        "typicality_rank",
        "typicality_exemplar",
        "typicality_rating",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def default_output_path(input_csv: Path) -> Path:
    return input_csv.with_name(f"{input_csv.stem}_jaccard_typicality_rankings.csv")


def default_plot_path(input_csv: Path) -> Path:
    return input_csv.with_name(
        f"{input_csv.stem}_jaccard_typicality_scatter_by_category.svg"
    )


def compute_axis_limits(
    grouped_rows: dict[str, list[dict[str, Any]]],
) -> tuple[tuple[float, float], tuple[float, float]]:
    valid_rows = [
        row
        for rows in grouped_rows.values()
        for row in rows
        if row["jaccard"] is not None and row["typicality"] is not None
    ]
    if not valid_rows:
        raise ValueError("No rows with both Jaccard and typicality values available for plotting.")

    min_x = min(row["jaccard"] for row in valid_rows)
    max_x = max(row["jaccard"] for row in valid_rows)
    min_y = min(row["typicality"] for row in valid_rows)
    max_y = max(row["typicality"] for row in valid_rows)

    if math.isclose(min_x, max_x):
        min_x -= 0.05
        max_x += 0.05
    if math.isclose(min_y, max_y):
        min_y -= 1.0
        max_y += 1.0

    x_pad = max((max_x - min_x) * 0.06, 0.02)
    y_pad = max((max_y - min_y) * 0.06, 0.5)
    return (min_x - x_pad, max_x + x_pad), (min_y - y_pad, max_y + y_pad)


def configure_matplotlib_cache() -> None:
    cache_root = Path(tempfile.gettempdir()) / "codex-runtime-cache"
    mpl_cache = cache_root / "matplotlib"
    xdg_cache = cache_root / "xdg"
    mpl_cache.mkdir(parents=True, exist_ok=True)
    xdg_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_cache))
    os.environ.setdefault("XDG_CACHE_HOME", str(xdg_cache))


def write_scatter_plot(
    grouped_rows: dict[str, list[dict[str, Any]]],
    output_path: Path,
    jaccard_label: str = "Jaccard",
    typicality_label: str = "Typicality",
) -> None:
    configure_matplotlib_cache()

    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    categories = sorted(grouped_rows)
    if not categories:
        raise ValueError("No categories available for plotting.")

    cols = min(3, max(1, math.ceil(math.sqrt(len(categories)))))
    rows_count = math.ceil(len(categories) / cols)
    (x_min, x_max), (y_min, y_max) = compute_axis_limits(grouped_rows)

    fig, axes = plt.subplots(
        rows_count,
        cols,
        figsize=(cols * 5.0, rows_count * 4.0),
        squeeze=False,
    )
    fig.suptitle("Typicality vs. Jaccard by Category", fontsize=14)

    all_axes = axes.flatten()
    x_span = x_max - x_min
    y_span = y_max - y_min
    x_offset = max(x_span * 0.012, 0.002)
    y_offset = max(y_span * 0.015, 0.08)

    for ax, category in zip(all_axes, categories):
        valid_rows = [
            row
            for row in grouped_rows[category]
            if row["jaccard"] is not None and row["typicality"] is not None
        ]
        xs = [row["jaccard"] for row in valid_rows]
        ys = [row["typicality"] for row in valid_rows]

        ax.scatter(xs, ys, s=18, color="#0b5ea8")
        for row in valid_rows:
            ax.annotate(
                row["item"],
                (row["jaccard"], row["typicality"]),
                xytext=(row["jaccard"] + x_offset, row["typicality"] + y_offset),
                textcoords="data",
                fontsize=8.5,
                color="#111111",
            )

        ax.set_title(category)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel(jaccard_label)
        ax.set_ylabel(typicality_label)
        ax.grid(True, color="#e3e3e3", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=8.5)

    for ax in all_axes[len(categories):]:
        ax.axis("off")

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    grouped_rows = load_rows(
        input_csv,
        category_column=args.category_column,
        item_column=args.item_column,
        jaccard_column=args.jaccard_column,
        typicality_column=args.typicality_column,
    )
    output_rows = build_output_rows(grouped_rows)
    output_path = Path(args.out) if args.out else default_output_path(input_csv)
    write_output(output_rows, output_path)

    plot_path = (
        None
        if args.no_plot
        else Path(args.plot_out) if args.plot_out else default_plot_path(input_csv)
    )
    if plot_path is not None:
        write_scatter_plot(grouped_rows, plot_path)

    print(f"Read categories: {len(grouped_rows)}")
    print(f"Wrote ranking comparison: {output_path}")
    if plot_path is not None:
        print(f"Wrote scatter plots: {plot_path}")


if __name__ == "__main__":
    main()
