# Output Folder Structure

This document explains the current structure under `output/experiments/` after restructuring.

## 1) Top-Level

```text
output/experiments/
├── bmf/   # Image-processing / OTSU pipeline experiments (run-wise)
└── bmd/   # Boolean Matrix Decomposition results (single matrix per branch)
```

## 2) BMF Structure (run-wise experiments)

`bmf` is organized by:
- domain: `animals`, `artifacts`
- level: `category`, `exemplar`
- branch:
  - category level: `all`
  - exemplar level: `all`, `frequency`, `importance`, `random`

```text
output/experiments/bmf/
├── animals/
│   ├── category/all/
│   │   ├── leaderboard.csv
│   │   ├── 1..9/                  # each run folder
│   │   └── preferred/<run_id>/    # selected best run
│   └── exemplar/
│       ├── all/
│       ├── frequency/
│       ├── importance/
│       └── random/
│           ├── leaderboard.csv
│           ├── 1..9/
│           └── preferred/<run_id>/
└── artifacts/
    ├── category/all/
    └── exemplar/
        ├── all/
        ├── frequency/
        ├── importance/
        └── random/
```


## 2) Preferred Runs (current)

```text
animals/category/all                -> preferred/8
animals/exemplar/all                -> preferred/8
animals/exemplar/frequency          -> preferred/1
animals/exemplar/importance         -> preferred/4
animals/exemplar/random             -> preferred/4
artifacts/category/all              -> preferred/5
artifacts/exemplar/all              -> preferred/5
artifacts/exemplar/frequency        -> preferred/1
artifacts/exemplar/importance       -> preferred/4
artifacts/exemplar/random           -> preferred/9
```

## 3) BMD Structure (matrix-level comparison)

`bmd` is organized similarly by domain/level/branch, but each branch stores a single matrix pair:

```text
output/experiments/bmd/
├── animals/
│   ├── category/all/
│   └── exemplar/{frequency,importance,random}/
└── artifacts/
    ├── category/all/
    └── exemplar/{frequency,importance,random}/
```

### Files inside each BMD branch folder

- `data_matrix.csv`
- `model_matrix.csv`
- `overall_jaccard.txt`
- `correlation_analysis_results.csv`
- `typicality_similarity_enriched.csv`
- `processing_duration.txt`
- `empty_rows_cols_stats.txt`

## 4) Quick Navigation

- BMF leaderboards:
  - `output/experiments/bmf/animals/.../leaderboard.csv`
  - `output/experiments/bmf/artifacts/.../leaderboard.csv`
- Preferred run outputs: `.../preferred/<run_id>/`
- BMD summary metrics: `output/experiments/bmd/.../overall_jaccard.txt`

