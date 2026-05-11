# Metrics In Label-Category Mapping

This project compares:
- **Label / Bundle**: a detected group from your algorithm (for example `label = 11`)
- **Category**: ground-truth class from `data/animals/typicality_ratings.csv` (`birds`, `fish`, `insects`, `mammals`, `reptiles`)

Use these counts:
- `n(label, category)`: number of exemplars of `category` inside `label`
- `n(label)`: total exemplars inside `label`
- `n(category)`: total exemplars in that ground-truth category

## Purity
Purity tells how "clean" a detected label is.

For a label `L`:

`purity(L) = max_c n(L, c) / n(L)`

Interpretation:
- High purity means most members of that label come from one category.
- Low purity means the label is mixed.

## Precision (for a mapped pair label -> category)
If label `L` is assigned to category `C`:

`precision(L -> C) = n(L, C) / n(L)`

Interpretation:
- Of all items predicted as category `C` via label `L`, how many are actually `C`?

## Recall (for a mapped pair label -> category)
If label `L` is assigned to category `C`:

`recall(L -> C) = n(L, C) / n(C)`

Interpretation:
- Of all true items in category `C`, how many were captured by label `L`?

## F-Score (F1)
Combines precision and recall into one number:

`F1 = 2 * (precision * recall) / (precision + recall)`

Interpretation:
- High only when both precision and recall are high.
- Useful when you want a balance between clean labels and good coverage.

## Incidence Density by Boolean Matrix Decomposition

Bundle density in model matrix:
- Bundle 1: `2013/7425 = 0.2711`
- Bundle 2: `2130/6750 = 0.3156`
- Bundle 3: `1440/4500 = 0.3200`
- Bundle 4: `1742/5850 = 0.2978`
- Bundle 5: `1580/4500 = 0.3511`

Bundle density in base matrix:
- Bundle 1: `2250/7425 = 0.3030`
- Bundle 2: `2222/6750 = 0.3292`
- Bundle 3: `1455/4500 = 0.3233`
- Bundle 4: `1799/5850 = 0.3075`
- Bundle 5: `1601/4500 = 0.3558`

Since there are no rectangles in boolean matrix decomposition, took all the attributes. It is just prototype clustering (Making rows in a cluster exactly same as it's prototype).

Therefore, we can't compare rectangles by index between boolean matrix decompositon and bmf (image processing / otsu).

## Visualization
- (1. decision) are the image processing bundles are overlapping?
    -> visualized or explained

    The image-processing bundles for run 7 form a partition (disjoint bundles), not overlapping.
    
    - Checked:
        - Cell-level overlap: same (row_new, col_new) belonging to multiple labels
        - Result: 0 multi-label cells out of 29025.
        - Rectangle overlap (red bundle bounding boxes, labels 2..14):
        - Result: 0 overlapping label pairs.

## Steps to run:
1. MATLAB step (create label assignments)
- Open `run.m` in MATLAB / MATLAB Online.
- Set the run parameters, for example:
```matlab
labeledMatrix = deleni(matrix, labeledMatrix, 1, true, 1, 16, 20, 0.55); % run 7
```
- Export `label_membership_cells.csv` and place it in:
`output/experiments/bmf/animals/category/all/<run_id>/label_membership_cells.csv`

Default runs root used by scripts:
`output/experiments/bmf/animals/category/all`

2. Prepare Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy scipy
```

3. Build normalized feature frequencies (one-time / when XLS changes)
```bash
./.venv/bin/python scripts/extract_sum_freq_normalized.py
```
This creates `data/animals/sum_features_freq_normalized.csv`.

4. Build dichotomized exemplar feature matrix (optional, exemplar-level workflow)
```bash
./.venv/bin/python scripts/dichotomize_leuven_matrix.py
```
This reads `data/animals/TypeIIAnimalExemplarFeatureMatrix.xls` and creates
`data/animals/animal_exemplar_feature_matrix_dichotomized.csv`.

5. Run label/category analysis for one run (updates run outputs + leaderboard)
Example for run 7:
```bash
./.venv/bin/python scripts/extract_animals_by_label.py \
  --run 7 \
  --param isColumnSplit=true \
  --param max_col=16 \
  --param max_row=20 \
  --param prah=0.55
```

6. Generate visualization for one run
```bash
./.venv/bin/python scripts/visualize_bundles.py --run 7
```
Output: `output/experiments/bmf/animals/category/all/7/bundle_overlay.svg`

7. Reconstruct matrix from selected labels (`best_distinct_mapping`)
```bash
./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py 7
```
Output: `output/experiments/bmf/animals/category/all/7/reconstructed_matrix.csv`

8. Run correlation analysis for one run
```bash
./.venv/bin/python scripts/correlation_analysis.py --run 7
```
Outputs:
- `output/experiments/bmf/animals/category/all/7/correlation_analysis_results.csv`
- `output/experiments/bmf/animals/category/all/7/typicality_similarity_enriched.csv`

9. Batch commands (all runs except run 5)
```bash
for run in 1 2 3 4 6 7 8 9; do
  ./.venv/bin/python scripts/visualize_bundles.py --run "$run"
  ./.venv/bin/python scripts/reconstruct_matrix_from_best_mapping.py "$run"
  ./.venv/bin/python scripts/correlation_analysis.py --run "$run"
done
```

## Steps to execute exemplar animals run:
----------------------
```bash
python scripts/extract_animals_by_label.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/all \
  --animals data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --feature-freq data/animals/sum_features_freq_normalized_exemplar.csv \
  --typicality data/animals/typicality_ratings.csv \
  --param isColumnSplit=false \
  --param max_col=15 \
  --param max_row=15 \
  --param prah=0.60

python scripts/visualize_bundles.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/all \
  --base-matrix data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --typicality data/animals/typicality_ratings.csv

python scripts/reconstruct_matrix_from_best_mapping.py 1 \
  --runs-root output/experiments/bmf/animals/exemplar/all \
  --rows 129 \
  --cols 764

python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/exemplar/all \
  --input-path data/animals/animal_exemplar_feature_matrix_dichotomized.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

## To run this command (matrix stats for all preferred runs)
Copy-paste this single command block to generate `model_matrix_stats.txt` for all 10 preferred BMF runs.

```bash
while read -r input freq; do
  ./.venv/bin/python scripts/matrix_stats.py --input "$input" --feature-freq-path "$freq"
done << 'EOF'
output/experiments/bmf/animals/category/all/preferred/8/reconstructed_matrix.csv data/animals/sum_features_freq_normalized.csv
output/experiments/bmf/animals/exemplar/all/preferred/8/reconstructed_matrix.csv data/animals/sum_features_freq_normalized_exemplar.csv
output/experiments/bmf/animals/exemplar/frequency/preferred/1/reconstructed_matrix.csv data/animals/sum_features_freq_normalized_exemplar.csv
output/experiments/bmf/animals/exemplar/importance/preferred/4/reconstructed_matrix.csv data/animals/sum_features_freq_normalized_exemplar.csv
output/experiments/bmf/animals/exemplar/random/preferred/4/reconstructed_matrix.csv data/animals/sum_features_freq_normalized_exemplar.csv
output/experiments/bmf/artifacts/category/all/preferred/5/reconstructed_matrix.csv data/artifacts/sum_features_freq_normalized_artifacts_category.csv
output/experiments/bmf/artifacts/exemplar/all/preferred/5/reconstructed_matrix.csv data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv
output/experiments/bmf/artifacts/exemplar/frequency/preferred/1/reconstructed_matrix.csv data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv
output/experiments/bmf/artifacts/exemplar/importance/preferred/4/reconstructed_matrix.csv data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv
output/experiments/bmf/artifacts/exemplar/random/preferred/9/reconstructed_matrix.csv data/artifacts/sum_features_freq_normalized_artifacts_exemplar.csv
EOF
```

This creates `model_matrix_stats.txt` in each corresponding folder.
