# Artifacts Workflow (Two Branches)

This README has two parallel branches:
- `artifacts/category/all`
- `artifacts/exemplar/all`

Both use:
- `data/artifacts/typicality_ratings.csv`

## 1. Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scipy
```

## 2. Common input file
Typicality file (required columns):
- `category`
- `exemplar`
- `typicality_rating`

Path:
- `data/artifacts/typicality_ratings.csv`

## 3. Branch A: artifacts/category/all

### 3.1 Build category feature-frequency file (from Type IV)
```bash
./.venv/bin/python scripts/extract_sum_freq_normalized.py \
  --input-xls data/artifacts/TypeIVArtifactsCategoryFeaturesMatrix.xls \
  --sheet sum \
  --out data/artifacts/sum_features_freq_normalized_artifacts_category.csv
```

### 3.2 Build category dichotomized matrix (from Type IV)
```bash
./.venv/bin/python scripts/dichotomize_leuven_matrix.py \
  --input-xls data/artifacts/TypeIVArtifactsCategoryFeaturesMatrix.xls \
  --out data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
  --name artifacts
```

### 3.3 Get matrix size (for reconstruction)
```bash
./.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_csv("data/artifacts/artifact_category_feature_matrix_dichotomized.csv")
print("rows =", len(df))
print("cols =", df.shape[1] - 1)
PY
```

### 3.4 Per-run MATLAB export
Put each run CSV at:
- `output/experiments/bmf/artifacts/category/all/<run_id>/label_membership_cells.csv`

### 3.5 Execute one run (example: run 1)
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/category/all \
  --animals data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
  --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_category.csv \
  --typicality data/artifacts/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/category/all \
  --base-matrix data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
  --typicality data/artifacts/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/artifacts/category/all \
  --rows 166 \
  --cols 301

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/category/all \
  --input-path data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
  --typicality-path data/artifacts/typicality_ratings.csv \
  --domain artifacts \
  --similarity-measure jaccard
```

### 3.6 Execute all runs (1..9)
```bash
for run in 1 2 3 4 5 6 7 8 9; do
  ./.venv/bin/python scripts/extract_animals_by_label.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/category/all \
    --animals data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
    --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_category.csv \
    --typicality data/artifacts/typicality_ratings.csv

  ./.venv/bin/python scripts/visualize_bundles.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/category/all \
    --base-matrix data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
    --typicality data/artifacts/typicality_ratings.csv

  ./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py "$run" \
    --runs-root output/experiments/bmf/artifacts/category/all \
    --rows <ROWS_FROM_3_3> \
    --cols <COLS_FROM_3_3>

  ./.venv/bin/python scripts/correlation_analysis.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/category/all \
    --input-path data/artifacts/artifact_category_feature_matrix_dichotomized.csv \
    --typicality-path data/artifacts/typicality_ratings.csv \
    --domain artifacts \
    --similarity-measure jaccard
done
```

## 4. Branch B: artifacts/exemplar/all

### 4.1 Build exemplar feature-frequency file (from Type II)
```bash
./.venv/bin/python scripts/extract_sum_freq_normalized.py \
  --input-xls data/artifacts/TypeIIArtifactsExemplarFeatureMatrix.xls \
  --sheet sum \
  --out data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv
```

### 4.2 Build exemplar dichotomized matrix (from Type II)
```bash
./.venv/bin/python scripts/dichotomize_leuven_matrix.py \
  --input-xls data/artifacts/TypeIIArtifactsExemplarFeatureMatrix.xls \
  --out data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
  --name artifacts
```

### 4.3 Get matrix size (for reconstruction)
```bash
./.venv/bin/python - <<'PY'
import pandas as pd
df = pd.read_csv("data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv")
print("rows =", len(df))
print("cols =", df.shape[1] - 1)
PY
```

### 4.4 Per-run MATLAB export
Put each run CSV at:
- `output/experiments/bmf/artifacts/exemplar/all/<run_id>/label_membership_cells.csv`

### 4.5 Execute one run (example: run 1)
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/all \
  --animals data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
  --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv \
  --typicality data/artifacts/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

./.venv/bin/python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/all \
  --base-matrix data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
  --typicality data/artifacts/typicality_ratings.csv

./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/all \
  --rows 166 \
  --cols 1295

./.venv/bin/python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/artifacts/exemplar/all \
  --input-path data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
  --typicality-path data/artifacts/typicality_ratings.csv \
  --domain artifacts \
  --similarity-measure jaccard
```

### 4.6 Execute all runs (1..9)
```bash
for run in 1 2 3 4 5 6 7 8 9; do
  ./.venv/bin/python scripts/extract_animals_by_label.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/exemplar/all \
    --animals data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
    --feature-freq data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv \
    --typicality data/artifacts/typicality_ratings.csv

  ./.venv/bin/python scripts/visualize_bundles.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/exemplar/all \
    --base-matrix data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
    --typicality data/artifacts/typicality_ratings.csv

  ./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py "$run" \
    --runs-root output/experiments/bmf/artifacts/exemplar/all \
    --rows <ROWS_FROM_4_3> \
    --cols <COLS_FROM_4_3>

  ./.venv/bin/python scripts/correlation_analysis.py \
    --run "$run" \
    --runs-root output/experiments/bmf/artifacts/exemplar/all \
    --input-path data/artifacts/artifact_exemplar_feature_matrix_dichotomized.csv \
    --typicality-path data/artifacts/typicality_ratings.csv \
    --domain artifacts \
    --similarity-measure jaccard
done
```
