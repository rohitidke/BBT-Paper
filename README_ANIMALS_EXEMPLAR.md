# Animals Exemplar Workflow (frequency / importance / random)

This README is for running experiments under:
- `output/experiments/bmf/animals/exemplar/frequency`
- `output/experiments/bmf/animals/exemplar/importance`
- `output/experiments/bmf/animals/exemplar/random`

You already placed:
- `label_membership_cells.csv` for runs `1..9` in each branch folder.

## 1. Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scipy
```

## 2. Common Inputs

Typicality:
- `data/animals/typicality_ratings.csv`

Feature frequency weights:
- `data/animals/sum_features_freq_normalized_exemplar.csv`

Branch matrices (from BMD JSON conversion outputs):
- `output/experiments/bmd/animals/exemplar/frequency/data_matrix.csv`
- `output/experiments/bmd/animals/exemplar/importance/data_matrix.csv`
- `output/experiments/bmd/animals/exemplar/random/data_matrix.csv`

Matrix size for reconstruction in these branches:
- `rows = 129`
- `cols = 225`

## 3. Per-Run Pipeline (example: run 1)

Pick one branch and run these 4 commands.

### 3.1 frequency
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/frequency \
  --animals output/experiments/bmd/animals/exemplar/frequency/data_matrix.csv \
  --feature-freq data/animals/sum_features_freq_normalized_exemplar.csv \
  --typicality data/animals/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/frequency \
  --base-matrix output/experiments/bmd/animals/exemplar/frequency/data_matrix.csv \
  --typicality data/animals/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/animals/exemplar/frequency \
  --rows 129 \
  --cols 225

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/frequency \
  --input-path output/experiments/bmd/animals/exemplar/frequency/data_matrix.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

### 3.2 importance
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/importance \
  --animals output/experiments/bmd/animals/exemplar/importance/data_matrix.csv \
  --feature-freq data/animals/sum_features_freq_normalized_exemplar.csv \
  --typicality data/animals/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/importance \
  --base-matrix output/experiments/bmd/animals/exemplar/importance/data_matrix.csv \
  --typicality data/animals/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/animals/exemplar/importance \
  --rows 129 \
  --cols 225

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/importance \
  --input-path output/experiments/bmd/animals/exemplar/importance/data_matrix.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

### 3.3 random
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/random \
  --animals output/experiments/bmd/animals/exemplar/random/data_matrix.csv \
  --feature-freq data/animals/sum_features_freq_normalized_exemplar.csv \
  --typicality data/animals/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/random \
  --base-matrix output/experiments/bmd/animals/exemplar/random/data_matrix.csv \
  --typicality data/animals/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/animals/exemplar/random \
  --rows 129 \
  --cols 225

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/random \
  --input-path output/experiments/bmd/animals/exemplar/random/data_matrix.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

## 4. Execute All Runs (1..9) For One Branch (zsh-compatible)

Use this for `frequency`, `importance`, or `random` by changing `BRANCH`.

```zsh
BRANCH="frequency"  # change to: importance / random
RUNS_ROOT="output/experiments/bmf/animals/exemplar/${BRANCH}"
MATRIX="output/experiments/bmd/animals/exemplar/${BRANCH}/data_matrix.csv"
FEATURE_FREQ="data/animals/sum_features_freq_normalized_exemplar.csv"
TYPICALITY="data/animals/typicality_ratings.csv"

# zsh arrays are 1-based by default
ISCOL=(false true true true true true true false true)
MAX_COL=(15 15 15 18 18 10 16 16 16)
MAX_ROW=(15 15 20 22 22 10 20 20 20)
PRAH=(0.60 0.60 0.60 0.55 0.58 0.60 0.55 0.55 0.52)

for run in {1..9}; do
  ./.venv/bin/python scripts/extract_animals_by_label.py \
    --run "$run" \
    --runs-root "$RUNS_ROOT" \
    --animals "$MATRIX" \
    --feature-freq "$FEATURE_FREQ" \
    --typicality "$TYPICALITY" \
    --param isColumnSplit="${ISCOL[$run]}" \
    --param max_col="${MAX_COL[$run]}" \
    --param max_row="${MAX_ROW[$run]}" \
    --param prah="${PRAH[$run]}"

  ./.venv/bin/python scripts/visualize_bundles.py \
    --run "$run" \
    --runs-root "$RUNS_ROOT" \
    --base-matrix "$MATRIX" \
    --typicality "$TYPICALITY"

  ./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py "$run" \
    --runs-root "$RUNS_ROOT" \
    --rows 129 \
    --cols 225

  ./.venv/bin/python scripts/correlation_analysis.py \
    --run "$run" \
    --runs-root "$RUNS_ROOT" \
    --input-path "$MATRIX" \
    --typicality-path "$TYPICALITY" \
    --domain animal \
    --similarity-measure jaccard
done
```

## 5. Outputs per run

For each run folder:
- `animals_by_label.txt`
- `label_category_analysis.csv`
- `bundle_overlay.svg`
- `reconstructed_matrix.csv`
- `correlation_analysis_results.csv`
- `typicality_similarity_enriched.csv`
- `summary.txt`, `summary.json`
- `processing_duration.txt`
