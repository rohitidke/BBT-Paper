# Repository Modules and Workflows

This document gives a short overview of the reusable parts of the repository for:

- re-ordering
- correlation analysis
- typicality analysis
- attribute importance analysis

The project is mostly script-based rather than class-based. The main reusable class-like component is the `Goodness` utility in `scripts/goodness.py`; most workflows are implemented as Python scripts plus MATLAB functions.

## 1. Re-ordering

Re-ordering is implemented in MATLAB.

Main entry point:

- `matlab/public/run.m`

Relevant methods:

- `barycenter(M)` in `matlab/public/barycenter.m`
- `alternating(M, no_of_iterations)` in `matlab/public/alternating.m`
- `spectral_ordering(M)` in `matlab/public/spectral_ordering.m`
- `deleni(...)` in `matlab/public/deleni.m`

Workflow:

1. Load the binary object-attribute matrix `M`.
2. Apply one of the re-ordering methods, usually `barycenter(M)`.
3. Use `deleni(...)` to recursively split the reordered matrix into rectangular label regions.
4. Export `label_membership_cells.csv`.

The exported `label_membership_cells.csv` contains:

- `label`
- `row_new`
- `col_new`
- `row_orig`
- `col_orig`

This file is the bridge between MATLAB and the Python evaluation scripts.

Important considerations:

- MATLAB indices are 1-based.
- The Python scripts expect the exported original coordinates, especially `row_orig` and `col_orig`.
- The matrix used in MATLAB must correspond to the matrix later passed to the Python scripts.

## 2. Correlation Analysis

Correlation analysis is implemented in:

- `scripts/correlation_analysis.py`

Supporting similarity utilities are in:

- `scripts/goodness.py`

Relevant functions/classes:

- `GoodnessType`
- `Goodness`
- `compare_matrices(a, b, t)`
- `load_input_csv(input_path)`
- `load_output_csv(output_path)`
- `correlation_analysis.main(...)`

The workflow compares an original data matrix with a reconstructed/model matrix and then correlates row-wise model fit with human typicality ratings.

The supported similarity measures are:

- Jaccard
- Ruzicka
- Czekanowski

Typical command:

```bash
python scripts/correlation_analysis.py \
  --run 1 \
  --runs-root output/experiments/bmf/animals/category/all \
  --input-path data/animals/animal_feature_matrix_dichotomized.csv \
  --typicality-path data/animals/typicality_ratings.csv \
  --domain animal \
  --similarity-measure jaccard
```

Outputs:

- `correlation_analysis_results.csv`
- `typicality_similarity_enriched.csv`
- `processing_duration.txt`

Important considerations:

- The original and model matrices must have exactly the same shape.
- The original matrix must contain exemplar names in the first column.
- The reconstructed/model matrix is expected to be numeric only, without a header.
- The typicality file must contain `exemplar`, `category`, and `typicality_rating`.

For BMD JSON matrices, use:

- `scripts/correlation_analysis_bmd.py`
- `scripts/correlation_analysis_bmd_from_csv.py`

## 3. Typicality Analysis

Typicality analysis is mainly part of the correlation workflow.

Main scripts:

- `scripts/correlation_analysis.py`
- `scripts/rank_typicality_vs_jaccard.py`

Input files:

- `data/animals/typicality_ratings.csv`
- `data/artifacts/typicality_ratings.csv`

`correlation_analysis.py` does the main typicality analysis:

1. Computes row-wise similarity between the original matrix and model matrix.
2. Maps each exemplar to its similarity score.
3. Merges those scores with human typicality ratings.
4. Computes Pearson correlations overall and by category.
5. Writes an enriched table containing typicality, model fit, and bundle information.

`rank_typicality_vs_jaccard.py` can be run afterwards on `typicality_similarity_enriched.csv`. It creates side-by-side category rankings by:

- model fit / Jaccard score
- human typicality rating

Typical command:

```bash
python scripts/rank_typicality_vs_jaccard.py \
  output/experiments/bmf/animals/category/all/8/typicality_similarity_enriched.csv
```

Important considerations:

- Exemplar names must match between the matrix and typicality CSV.
- The script strips whitespace but does not perform fuzzy matching.
- The resulting correlations should be interpreted category-wise, not only overall.

## 4. Attribute Importance Analysis

Attribute importance appears in two related places:

1. as an attribute-filtering branch, for example `exemplar/importance`
2. as an enrichment variable in attribute-level output files

### Extracting Importance Ratings

Importance ratings are extracted from:

- `data/leuven_enhanced.json`

Using:

- `scripts/extract_importance_ratings_from_leuven.py`

Typical command:

```bash
python scripts/extract_importance_ratings_from_leuven.py data/leuven_enhanced.json
```

Outputs:

- `data/animals/importance_ratings_category.csv`
- `data/animals/importance_ratings_exemplar.csv`
- `data/artifacts/importance_ratings_category.csv`
- `data/artifacts/importance_ratings_exemplar.csv`

Each output contains:

- `features`
- `category`
- `importance_rating`

### Attribute-Level Enrichment

Attribute-level model analysis is implemented in:

- `scripts/attribute_weight_similarity_enrichment.py`

This script reads an experiment folder containing:

- `data_matrix.csv`
- `model_matrix.csv`

and writes:

- `attribute_weight_similarity_enriched.csv`

The enriched output includes:

- `attribute`
- `category`
- `bundles`
- `bundle_specific_attribute`
- `normalized_freq`
- `importance_rating`
- `columnwise_similarity`

Typical command:

```bash
python scripts/attribute_weight_similarity_enrichment.py \
  output/experiments/bmd/animals/exemplar/importance
```

Important considerations:

- Importance ratings are category-specific.
- The lookup key is effectively `(feature, category)`.
- Category labels are normalized internally, especially for artifact categories.
- Missing importance ratings are left empty in the enriched CSV.

## 5. Bundle and Model-Matrix Workflow

For BMF experiments, the typical workflow is:

1. Run MATLAB re-ordering and splitting.
2. Save `label_membership_cells.csv` into the relevant run folder.
3. Analyze label/category structure with `scripts/extract_animals_by_label.py`.
4. Reconstruct the model matrix with `scripts/reconstruct_matrix_from_best_mapping.py`.
5. Run correlation analysis with `scripts/correlation_analysis.py`.
6. Optionally enrich attributes with `scripts/attribute_weight_similarity_enrichment.py`.

Although `extract_animals_by_label.py` has "animals" in the filename, it is also used for artifacts when artifact input paths are passed.

Important outputs per run:

- `animals_by_label.txt`
- `label_category_analysis.csv`
- `summary.txt`
- `summary.json`
- `leaderboard.csv`
- `reconstructed_matrix.csv`
- `correlation_analysis_results.csv`
- `typicality_similarity_enriched.csv`
- `attribute_weight_similarity_enriched.csv`

## 6. Main Things to Check Before Reusing the Workflows

Before running an analysis, check:

- The original matrix and model matrix have the same number of rows and columns.
- The first column of the original matrix contains exemplar/object names.
- The reconstructed/model matrix has no header.
- The row and column order matches the original data.
- The typicality CSV uses the same exemplar names as the matrix.
- The selected domain paths are consistent: animals vs artifacts.
- The selected level paths are consistent: category vs exemplar.
- For filtered branches, use the matching matrix and feature-weight file.

The most common source of errors is misalignment between MATLAB-exported labels, matrix row/column order, and the Python evaluation inputs.
