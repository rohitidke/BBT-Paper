#!/usr/bin/env python3
"""Extract features + freq from the `sum` sheet and write normalized freq CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def find_feature_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        name = str(col).strip().lower()
        if "english" in name:
            return col
    raise ValueError("Could not find features column (expected a column containing 'ENGLISH').")


def find_freq_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        name = str(col).strip().lower()
        if name == "freq" or "freq" in name:
            return col

    # Fallback: some files use an unnamed header where first row value is "freq".
    for col in df.columns:
        series = df[col].astype(str).str.strip().str.lower()
        if series.eq("freq").any():
            return col

    raise ValueError("Could not find freq column.")


def normalize_min_max(values: pd.Series) -> pd.Series:
    vmin = values.min()
    vmax = values.max()
    if pd.isna(vmin) or pd.isna(vmax):
        return pd.Series([0.0] * len(values), index=values.index)
    if vmax == vmin:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - vmin) / (vmax - vmin)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create CSV with columns: features, freq, normalized_freq from XLS sheet 'sum'."
    )
    parser.add_argument(
        "--input-xls",
        default="data/animals/TypeIVAnimalCategoryFeatureMatrix.xls",
        help="Input XLS file path",
    )
    parser.add_argument(
        "--sheet",
        default="sum",
        help="Sheet name (default: sum)",
    )
    parser.add_argument(
        "--out",
        default="data/animals/sum_features_freq_normalized.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    xls_path = Path(args.input_xls)
    if not xls_path.exists():
        raise SystemExit(f"Input file not found: {xls_path}")

    df = pd.read_excel(xls_path, sheet_name=args.sheet)
    feature_col = find_feature_column(df)
    freq_col = find_freq_column(df)

    out = df[[feature_col, freq_col]].copy()
    out.columns = ["features", "freq"]
    out["features"] = out["features"].astype(str).str.strip()
    out["freq"] = pd.to_numeric(out["freq"], errors="coerce")

    # Keep only valid feature rows with numeric frequencies.
    out = out[(out["features"] != "") & (~out["features"].str.lower().eq("nan"))]
    out = out[out["freq"].notna()]
    out = out[out["features"].str.lower() != "feature / exemplar dutch"]

    out["normalized_freq"] = normalize_min_max(out["freq"]).round(6)
    out = out.reset_index(drop=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print(f"Input: {xls_path}")
    print(f"Sheet: {args.sheet}")
    print(f"Detected features column: {feature_col}")
    print(f"Detected freq column: {freq_col}")
    print(f"Rows written: {len(out)}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
