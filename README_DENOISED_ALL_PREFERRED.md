# Denoised Workflow: animals/exemplar/all/preferred/denoised

This guide runs the full workflow for:

- `output/experiments/bmf/animals/exemplar/all/preferred/denoised`

Expected input file:

- `output/experiments/bmf/animals/exemplar/all/preferred/denoised/label_membership_cells.csv`

## 1) Extract + metrics + leaderboard

```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run denoised \
  --runs-root output/experiments/bmf/animals/exemplar/all/preferred \
  --animals data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --feature-freq data/animals/sum_features_freq_normalized_exemplar.csv \
  --typicality data/animals/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=16 \
  --param max_row=20 \
  --param prah=0.55
```

## 2) Visualize bundles

```bash
./.venv/bin/python scripts/visualize_bundles.py \
  --run-dir output/experiments/bmf/animals/exemplar/all/preferred/denoised \
  --base-matrix data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --typicality data/animals/typicality_ratings.csv \
  --leaderboard output/experiments/bmf/animals/exemplar/all/preferred/leaderboard.csv
```

## 3) Reconstruct matrix

```bash
./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py denoised \
  --runs-root output/experiments/bmf/animals/exemplar/all/preferred \
  --rows 129 \
  --cols 764
```

## 4) Correlation analysis

```bash
./.venv/bin/python scripts/correlation_analysis.py \
  --run denoised \
  --runs-root output/experiments/bmf/animals/exemplar/all/preferred \
  --input-path data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

## 5) Matrix stats

```bash
./.venv/bin/python scripts/matrix_stats.py \
  --input output/experiments/bmf/animals/exemplar/all/preferred/denoised/reconstructed_matrix.csv \
  --feature-freq-path data/animals/sum_features_freq_normalized_exemplar.csv
```

