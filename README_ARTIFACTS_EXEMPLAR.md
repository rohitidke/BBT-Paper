# Artifacts Exemplar Workflow (frequency / importance / random)

This README is for running experiments under:
- `output/experiments/bmf/artifacts/exemplar/frequency`
- `output/experiments/bmf/artifacts/exemplar/importance`
- `output/experiments/bmf/artifacts/exemplar/random`

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
- `data/artifacts/typicality_ratings.csv`

Feature frequency weights:
- `data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv`

Branch matrices (from BMD JSON conversion outputs):
- `output/experiments/bmd/artifacts/exemplar/frequency/data_matrix.csv` (`rows=166`, `cols=149`)
- `output/experiments/bmd/artifacts/exemplar/importance/data_matrix.csv` (`rows=166`, `cols=153`)
- `output/experiments/bmd/artifacts/exemplar/random/data_matrix.csv` (`rows=166`, `cols=152`)

## 3. Per-Run Pipeline (example: run 1)

Pick one branch and run these 4 commands.

### 3.1 frequency
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/frequency \
  --animals output/experiments/bmd/artifacts/exemplar/frequency/data_matrix.csv \
  --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv \
  --typicality data/artifacts/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/frequency \
  --base-matrix output/experiments/bmd/artifacts/exemplar/frequency/data_matrix.csv \
  --typicality data/artifacts/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/frequency \
  --rows 166 \
  --cols 149

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/frequency \
  --input-path output/experiments/bmd/artifacts/exemplar/frequency/data_matrix.csv \
  --typicality-path data/artifacts/typicality_ratings.csv \
  --domain artifacts \
  --similarity-measure jaccard
```

### 3.2 importance
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/importance \
  --animals output/experiments/bmd/artifacts/exemplar/importance/data_matrix.csv \
  --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv \
  --typicality data/artifacts/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/importance \
  --base-matrix output/experiments/bmd/artifacts/exemplar/importance/data_matrix.csv \
  --typicality data/artifacts/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/importance \
  --rows 166 \
  --cols 153

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/importance \
  --input-path output/experiments/bmd/artifacts/exemplar/importance/data_matrix.csv \
  --typicality-path data/artifacts/typicality_ratings.csv \
  --domain artifacts \
  --similarity-measure jaccard
```

### 3.3 random
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/random \
  --animals output/experiments/bmd/artifacts/exemplar/random/data_matrix.csv \
  --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv \
  --typicality data/artifacts/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/random \
  --base-matrix output/experiments/bmd/artifacts/exemplar/random/data_matrix.csv \
  --typicality data/artifacts/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/random \
  --rows 166 \
  --cols 152

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/random \
  --input-path output/experiments/bmd/artifacts/exemplar/random/data_matrix.csv \
  --typicality-path data/artifacts/typicality_ratings.csv \
  --domain artifacts \
  --similarity-measure jaccard
```

## 4. Execute All Runs (1..9) For One Branch (zsh-compatible)

Use this for `frequency`, `importance`, or `random` by changing `BRANCH`.

```zsh
BRANCH="frequency"  # change to: importance / random
RUNS_ROOT="output/experiments/bmf/artifacts/exemplar/${BRANCH}"
MATRIX="output/experiments/bmd/artifacts/exemplar/${BRANCH}/data_matrix.csv"
FEATURE_FREQ="data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv"
TYPICALITY="data/artifacts/typicality_ratings.csv"

case "$BRANCH" in
  frequency) COLS=149 ;;
  importance) COLS=153 ;;
  random) COLS=152 ;;
  *) echo "Unsupported BRANCH: $BRANCH"; COLS="" ;;
esac
[ -n "$COLS" ] || { echo "Set BRANCH to: frequency | importance | random"; }

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
    --rows 166 \
    --cols "$COLS"

  ./.venv/bin/python scripts/correlation_analysis.py \
    --run "$run" \
    --runs-root "$RUNS_ROOT" \
    --input-path "$MATRIX" \
    --typicality-path "$TYPICALITY" \
    --domain artifacts \
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
