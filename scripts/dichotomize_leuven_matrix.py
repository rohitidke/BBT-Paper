#!/usr/bin/env python3
"""Convert Leuven Excel matrix files to dichotomized CSV files."""

import argparse
from pathlib import Path

import pandas as pd
import numpy as np


def dichotomize_matrix(
    input_file: str, output_file: str, threshold: int = 2, name: str = ""
) -> None:
    """
    Read the Excel file, apply majority rule dichotomization, and save as CSV.

    Args:
        input_file: Path to the input Excel file (.xls)
        output_file: Path to the output CSV file
        threshold: Values >= threshold become 1, values < threshold become 0 (default: 2)
    """
    # Read the 'sum' sheet from the Excel file
    print(f"Reading: {input_file}")
    df_sum = pd.read_excel(input_file, sheet_name="sum")

    # Extract feature names (English) - skip row 0 which contains Dutch exemplar names
    try:
        feature_names = df_sum["feature / exemplar ENGLISH"].iloc[1:].tolist()
    except KeyError:
        feature_names = df_sum["feature/ exemplar ENGLISH"].iloc[1:].tolist()

    # Extract exemplar names (English) - from column headers, skip first 3 columns
    # (Column 0: Dutch feature name, Column 1: English feature name, Column 2: freq)
    exemplar_names = df_sum.columns[3:].tolist()

    # Extract the data matrix (rows 1 onwards, columns 3 onwards)
    data_matrix = df_sum.iloc[1:, 3:].values.astype(float)

    # Apply majority rule dichotomization
    data_dichotomized = np.where(data_matrix >= threshold, 1, 0)

    # Create DataFrame with exemplars as rows and features as columns
    df_result = pd.DataFrame(
        data_dichotomized.T,  # Transpose so exemplars are rows
        index=exemplar_names,
        columns=feature_names,
    )
    df_result.index.name = name

    # Save to CSV
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    df_result.to_csv(output_file)

    # Print summary
    print(f"Output: {output_file}")
    print(
        f"Matrix shape: {df_result.shape[0]} exemplars x {df_result.shape[1]} features"
    )
    print(
        f"Dichotomization rule: values < {threshold} -> 0, values >= {threshold} -> 1"
    )
    print(f"0s (feature doesn't apply): {np.sum(data_dichotomized == 0):,}")
    print(f"1s (feature applies):       {np.sum(data_dichotomized == 1):,}")
    print(f"Density (proportion of 1s): {np.mean(data_dichotomized):.2%}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Dichotomize Leuven feature matrix (0/1) using threshold rule "
            "(default: values >= 2 -> 1, else 0)."
        )
    )
    parser.add_argument(
        "--input-xls",
        default="data/animals/TypeIIAnimalExemplarFeatureMatrix.xls",
        help="Input Excel file path",
    )
    parser.add_argument(
        "--out",
        default="data/animals/animal_exemplar_feature_matrix_dichotomized.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=2,
        help="Dichotomization threshold (default: 2)",
    )
    parser.add_argument(
        "--name",
        default="animal",
        help="Index label name for CSV (default: animal)",
    )
    args = parser.parse_args()

    dichotomize_matrix(
        input_file=args.input_xls,
        output_file=args.out,
        threshold=args.threshold,
        name=args.name,
    )


if __name__ == "__main__":
    main()
