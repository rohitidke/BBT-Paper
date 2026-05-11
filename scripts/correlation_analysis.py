#!/usr/bin/env python3
"""
Correlation analysis between model goodness and typicality ratings.

This script:
1. Loads base and reconstructed incidence CSVs
2. Compares matrices using Jaccard (via goodness.compare_matrices)
3. Merges row-wise similarity scores with typicality ratings
4. Computes Pearson correlation by category
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr

from goodness import GoodnessType, compare_matrices

DEFAULT_RUNS_ROOT = "output/experiments/bmf/animals/category/all"
DEFAULT_INPUT_PATH = "data/animals/animal_feature_matrix_dichotomized.csv"
DEFAULT_TYPICALITY_PATH = "data/animals/typicality_ratings.csv"


def load_input_csv(input_path: Path) -> tuple[list[str], object]:
    """Load base incidence CSV (first column = exemplar names)."""
    df = pd.read_csv(input_path)
    if df.shape[1] < 2:
        raise ValueError(f"Invalid input CSV (needs at least 2 columns): {input_path}")

    objects = df.iloc[:, 0].astype(str).str.strip().tolist()
    incidences = (
        df.iloc[:, 1:]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .to_numpy()
    )
    incidences = (incidences > 0).astype(int)
    return objects, incidences


def load_output_csv(output_path: Path) -> object:
    """Load reconstructed incidence CSV (no header)."""
    df = pd.read_csv(output_path, header=None)
    incidences = df.apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy()
    incidences = (incidences > 0).astype(int)
    return incidences


def append_processing_duration(run_dir: Path, script_name: str, seconds: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "processing_duration.txt"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{script_name}\t{seconds:.3f}\n")


def update_leaderboard_overall_jaccard(
    runs_root: str,
    run_id: str,
    overall_jaccard: float,
) -> None:
    """Update leaderboard with overall_jaccard and sort descending by it."""
    leaderboard_path = Path(runs_root) / "leaderboard.csv"
    if not leaderboard_path.exists():
        print(f"Warning: leaderboard not found, skipping update: {leaderboard_path}")
        return

    with leaderboard_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        print(f"Warning: leaderboard is empty, skipping update: {leaderboard_path}")
        return

    # Keep overall_jaccard as the last column.
    fieldnames = [c for c in fieldnames if c != "overall_jaccard"] + ["overall_jaccard"]

    found = False
    for row in rows:
        if str(row.get("run_id", "")).strip() == str(run_id).strip():
            row["overall_jaccard"] = f"{overall_jaccard:.6f}"
            found = True
        else:
            row.setdefault("overall_jaccard", "")

    if not found:
        print(f"Warning: run_id={run_id} not found in leaderboard: {leaderboard_path}")
        return

    def sort_key(row: dict[str, str]) -> float:
        raw = str(row.get("overall_jaccard", "")).strip()
        try:
            return float(raw)
        except ValueError:
            return float("-inf")

    rows.sort(key=sort_key, reverse=True)

    with leaderboard_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        "Leaderboard updated and sorted by overall_jaccard: "
        f"{leaderboard_path}"
    )


def main(
    input_path: str,
    output_path: str,
    typicality_path: str = DEFAULT_TYPICALITY_PATH,
    domain: str = "animal",
    similarity_measure: str = "jaccard",
    exclude: bool = False,
    run_id: str | None = None,
    runs_root: str | None = None,
) -> None:
    """
    Main function for correlation analysis.

    Args:
        input_path: Path to original incidence CSV
        output_path: Path to reconstructed incidence CSV
        typicality_path: Path to typicality ratings CSV
        domain: Domain name (default: "animal")
        similarity_measure: "jaccard", "ruzicka", or "czekanowski" (default: "jaccard")
        exclude: Optional exclusion mode (kept for compatibility)
    """

    started = time.perf_counter()
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        return
    if not output_path.exists():
        print(f"Error: Output file '{output_path}' not found")
        return

    run_dir = output_path.parent

    print("Loading incidence CSV data...")
    print(f"  Base data: {input_path}")
    print(f"  Model data: {output_path}")

    # Load CSVs instead of HCM.
    exemplar_names, base_incidences = load_input_csv(input_path)
    model_incidences = load_output_csv(output_path)

    print(f"\nBase matrix shape: {base_incidences.shape}")
    print(f"Model matrix shape: {model_incidences.shape}")

    if base_incidences.shape != model_incidences.shape:
        print(
            f"Error: matrix shape mismatch: base={base_incidences.shape}, model={model_incidences.shape}"
        )
        return

    # Map string parameter to GoodnessType enum.
    if similarity_measure.lower() == "jaccard":
        goodness_type = GoodnessType.JACCARD
        measure_name = "Jaccard"
    elif similarity_measure.lower() == "ruzicka":
        goodness_type = GoodnessType.RUZICKA
        measure_name = "Ruzicka"
    elif similarity_measure.lower() == "czekanowski":
        goodness_type = GoodnessType.CZEKANOWSKI
        measure_name = "Czekanowski"
    else:
        print(
            f"Error: Unknown similarity measure '{similarity_measure}'. "
            "Use 'jaccard', 'ruzicka', or 'czekanowski'."
        )
        return

    print(f"\nComputing {measure_name} similarity...")
    goodness = compare_matrices(base_incidences, model_incidences, goodness_type)

    rowwise_similarity = goodness.rows
    print(f"  Row-wise {measure_name} scores: {len(rowwise_similarity)} rows")
    print(f"  Overall {measure_name}: {goodness.total:.4f}")
    print(f"  Exemplars in input data: {len(exemplar_names)} exemplars")

    typicality_file = Path(typicality_path)
    if not typicality_file.exists():
        print(f"Error: Typicality file '{typicality_file}' not found")
        return

    print(f"\nLoading typicality ratings from: {typicality_file}")
    df = pd.read_csv(typicality_file)
    required_cols = {"exemplar", "category", "typicality_rating"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        print(
            f"Error: Typicality file is missing required columns: {sorted(missing_cols)}"
        )
        return

    df["exemplar"] = df["exemplar"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["typicality_rating"] = pd.to_numeric(df["typicality_rating"], errors="coerce")
    unique_exemplars = df["exemplar"].unique()
    print(f"  Found {len(unique_exemplars)} unique exemplars in typicality data")

    if len(exemplar_names) != len(rowwise_similarity):
        print(
            f"Error: Number of exemplar names ({len(exemplar_names)}) doesn't match number "
            f"of {measure_name} scores ({len(rowwise_similarity)})"
        )
        return

    exemplar_similarity_map = {
        str(exemplar).strip(): float(score)
        for exemplar, score in zip(exemplar_names, rowwise_similarity)
    }

    df["rowwise_similarity"] = df["exemplar"].map(
        lambda x: exemplar_similarity_map.get(str(x).strip())
    )

    # Assign bundle ids based on unique reconstructed row patterns.
    bundle_by_pattern: dict[tuple[int, ...], int] = {}
    exemplar_bundle_map: dict[str, int] = {}
    for exemplar, incidence_row in zip(exemplar_names, model_incidences):
        pattern = tuple(int(v) for v in incidence_row.tolist())
        if pattern not in bundle_by_pattern:
            bundle_by_pattern[pattern] = len(bundle_by_pattern) + 1
        exemplar_bundle_map[str(exemplar).strip()] = bundle_by_pattern[pattern]

    df["bundles"] = df["exemplar"].map(lambda x: exemplar_bundle_map.get(str(x).strip())).astype("Int64")
    print(f"  Found {len(bundle_by_pattern)} unique bundles in model incidences")

    if exclude is True:
        if domain == "artifacts":
            excluded_exemplars = {
                "scissors",
                "knife",
                "axe",
                "drill",
                "hammer",
                "pickaxe",
                "crowbar",
                "shovel",
                "grinding disc",
                "saw",
                "tank",
                "go-cart",
                "cart",
                "skateboard",
                "sled",
                "kick scooter",
                "lawn mower",
                "rope",
                "apron",
            }
            before_drop = len(df)
            df = df[~df["exemplar"].isin(excluded_exemplars)]
            dropped = before_drop - len(df)
            if dropped:
                print(f"  Dropped {dropped} artifacts before analysis")
        if domain == "animal":
            # category-level
            excluded_exemplars = {
                "squid", 
                "caiman", 
                "crocodile",
                "alligator",
                "mouse",
                "bat",
                "toad",
                "ostrich",
                "penguin",
                "heron",
                "peacock",
                "seagull",
                "worm",
                "turkey",
                "pheasant",
                "chicken",
                "leech",
                "dove",
                "rooster",
                "crow",
                "magpie",
                "cuckoo",
                "parakeet",
                "woodpecker",
                "canary",
                "blackbird",
                "swallow",
                "robin",
                "sparrow",
                "chickadee"
            }
            before_drop = len(df)
            df = df[~df["exemplar"].isin(excluded_exemplars)]
            dropped = before_drop - len(df)
            if dropped:
                print(f"  Dropped {dropped} animals before analysis")

    unmapped = df[df["rowwise_similarity"].isna()]["exemplar"].unique()
    if len(unmapped) > 0:
        print(
            f"\nWarning: {len(unmapped)} exemplars couldn't be mapped to {measure_name} scores:"
        )
        print(f"  First few unmapped: {unmapped[:5].tolist()}")

    unmapped_bundles = df[df["bundles"].isna()]["exemplar"].unique()
    if len(unmapped_bundles) > 0:
        print(
            f"\nWarning: {len(unmapped_bundles)} exemplars couldn't be mapped to bundles:"
        )
        print(f"  First few unmapped: {unmapped_bundles[:5].tolist()}")

    mapped_sample = df[df["rowwise_similarity"].notna()].head(3)
    if not mapped_sample.empty:
        print("\nSample of successful mappings:")
        for _, row in mapped_sample.iterrows():
            print(
                f"  {row['exemplar']:20s} -> {measure_name}: {row['rowwise_similarity']:.4f}"
            )

    print("\nDataframe after merging similarity scores:")
    print(df.head())

    print("\n" + "=" * 80)
    print("BUNDLE DISTRIBUTION BY CATEGORY (COUNTS):")
    print("=" * 80)
    bundle_distribution = (
        df.dropna(subset=["bundles"])
        .groupby(["category", "bundles"])
        .size()
        .unstack(fill_value=0)
        .sort_index(axis=1)
    )
    print(bundle_distribution)

    if not df["rowwise_similarity"].isna().all():
        valid_data = df[["typicality_rating", "rowwise_similarity"]].dropna()
        if len(valid_data) > 1:
            correlation, p_value = pearsonr(
                valid_data["typicality_rating"], valid_data["rowwise_similarity"]
            )
            print(
                f"\nOverall Pearson correlation: r = {correlation:.4f}, p-value = {p_value:.6f}"
            )

    print("\n" + "=" * 80)
    print("BY CATEGORY:")
    print("=" * 80)
    category_stats = (
        df.groupby("category")
        .agg(
            {
                "typicality_rating": "mean",
                "rowwise_similarity": "mean",
                "exemplar": "count",
            }
        )
        .round(4)
    )
    category_stats.columns = ["avg_typicality", f"avg_{similarity_measure}", "count"]
    print(category_stats)

    print("\n" + "=" * 80)
    print("PEARSON CORRELATION BY CATEGORY:")
    print("=" * 80)

    correlations: list[dict[str, object]] = []
    for category in df["category"].unique():
        category_df = df[df["category"] == category].dropna(
            subset=["rowwise_similarity", "typicality_rating"]
        )
        if len(category_df) > 1:
            corr, p_value = pearsonr(
                category_df["typicality_rating"], category_df["rowwise_similarity"]
            )
            significance = (
                "highly significant"
                if p_value < 0.001
                else "very significant"
                if p_value < 0.01
                else "significant"
                if p_value < 0.05
                else "not significant"
            )
            correlations.append(
                {
                    "category": category,
                    "correlation": round(float(corr), 6),
                    "p_value": round(float(p_value), 6),
                    "n_samples": len(category_df),
                    "significance": significance,
                }
            )
            print(
                f"{category:20s}: r = {corr:+.6f}, p = {p_value:.6f} "
                f"{significance} (n = {len(category_df)})"
            )
        else:
            print(f"{category:20s}: Insufficient data for correlation")

    if correlations:
        corr_df = pd.DataFrame(correlations)
        print("\n" + "=" * 80)
        print("CORRELATION SUMMARY:")
        print("=" * 80)
        print(f"Mean correlation across categories: {corr_df['correlation'].mean():.4f}")
        print(f"Std deviation: {corr_df['correlation'].std():.4f}")
        print(
            f"Min correlation: {corr_df['correlation'].min():.4f} "
            f"({corr_df.loc[corr_df['correlation'].idxmin(), 'category']})"
        )
        print(
            f"Max correlation: {corr_df['correlation'].max():.4f} "
            f"({corr_df.loc[corr_df['correlation'].idxmax(), 'category']})"
        )

        output_dir = output_path.parent
        results_csv = output_dir / "correlation_analysis_results.csv"
        enriched_csv = output_dir / "typicality_similarity_enriched.csv"
        corr_df.to_csv(results_csv, index=False)
        df.to_csv(enriched_csv, index=False)

        print("\n" + "=" * 80)
        print("COMPLETE RESULTS TABLE:")
        print("=" * 80)
        print(corr_df.to_string(index=False))
        print(f"\nResults saved to: {results_csv}")
        print(f"Enriched table saved to: {enriched_csv}")

    elapsed = time.perf_counter() - started

    if (
        run_id is not None
        and runs_root is not None
        and similarity_measure.lower() == "jaccard"
    ):
        update_leaderboard_overall_jaccard(
            runs_root=runs_root,
            run_id=run_id,
            overall_jaccard=float(goodness.total),
        )

    append_processing_duration(run_dir, "correlation_analysis.py", elapsed)
    print(f"Processing duration: {elapsed:.3f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run correlation analysis for one experiment run.")
    parser.add_argument("--run", required=True, help="Run id, e.g. 5")
    parser.add_argument(
        "--runs-root",
        default=DEFAULT_RUNS_ROOT,
        help=f"Runs root directory (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--input-path",
        default=DEFAULT_INPUT_PATH,
        help=f"Base incidence CSV path (default: {DEFAULT_INPUT_PATH})",
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        default=None,
        help=(
            "Model incidence CSV path override "
            "(default: <runs-root>/<run>/reconstructed_matrix.csv)"
        ),
    )
    parser.add_argument(
        "--typicality-path",
        default=DEFAULT_TYPICALITY_PATH,
        help=f"Typicality ratings CSV path (default: {DEFAULT_TYPICALITY_PATH})",
    )
    parser.add_argument(
        "--domain",
        default="animal",
        help="Domain for optional exclusion logic (default: animal)",
    )
    parser.add_argument(
        "--similarity-measure",
        default="jaccard",
        choices=["jaccard", "ruzicka", "czekanowski"],
        help="Similarity measure to use (default: jaccard)",
    )
    parser.add_argument(
        "--exclude",
        action="store_true",
        help="Enable domain-specific exemplar exclusions (default: False)",
    )
    args = parser.parse_args()

    # Keep old script style: define paths here, call main().
    input_file = args.input_path
    output_file = (
        args.output_file
        if args.output_file
        else f"{args.runs_root}/{args.run}/reconstructed_matrix.csv"
    )
    typicality_file = args.typicality_path
    domain = args.domain
    similarity_measure = args.similarity_measure
    exclude = args.exclude

    main(
        input_path=input_file,
        output_path=output_file,
        typicality_path=typicality_file,
        domain=domain,
        similarity_measure=similarity_measure,
        exclude=exclude,
        run_id=args.run,
        runs_root=args.runs_root,
    )
