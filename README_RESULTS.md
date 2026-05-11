# Results Summary

## 1) Goal
This document summarizes results from Boolean matrix factorisation(image processing) experiments across:
- Animals / Category / All
- Animals / Exemplar / All
- Artifacts / Category / All
- Artifacts / Exemplar / All

Each branch contains **9 runs** with different `deleni` parameters.

## 2) What Was Evaluated
For each run, we evaluated three aspects:

1. **Bundle purity quality**
- Metric: `weighted_purity_percent` from `leaderboard.csv`
- Higher means bundles are more category-consistent.

2. **Distinct category matching**
- Metric: `distinct_category_match_accuracy_percent` from `leaderboard.csv`
- Higher means better one-label-per-category matching quality.

3. **Typicality correlation quality**
- Source: `correlation_analysis_results.csv`
- We tracked:
- mean Pearson correlation across categories
- number of categories with **positive and significant** correlation (`r > 0` and `p < 0.05`)

## 2.1) Leaderboard Metric Definitions 

These are the exact metrics used in `leaderboard.csv`:

1. `mean_purity_percent`
- Average of per-label purity across all labels.
- Formula: `mean(purity_percent(label))`
- Per-label purity formula:
  `purity_percent(label) = 100 * dominant_count(label) / count(label)`

2. `weighted_purity_percent`
- Purity weighted by label size (object count).
- Formula: `weighted_mean(purity_percent(label))`

3. `distinct_category_match_count`
- Total correctly matched objects from the selected one-label-per-category mapping.
- Formula: `sum(matched_count(category -> selected_label))`

4. `distinct_category_match_accuracy_percent`
- Normalized distinct mapping/match score against all category objects.
- Formula: `100 * distinct_category_match_count / sum(category_totals)`

5. `best_distinct_mapping`
- Final selected mapping list: one label per category with fields such as
  `category`, `label`, `matched_count`, `purity_percent`, `recall_percent`, `f1_percent`.
- `label`: selected label for that category
- `matched_count`: number of objects of that category inside that label
- `purity_percent`: matched_count/total_count_label
- `recall_percent`: matched_count/totla_count_category
- `f1_percent`: Combined score of purity_percent and recall_percent, just like f1-score.

## 3) Dataset Branches
- Animals categories: 5 (`birds`, `fish`, `insects`, `mammals`, `reptiles`)
- Artifacts categories: 6 (`clothing`, `kitchen utensils`, `musical instruments`, `tools`, `vehicles`, `weapons`)

## 4) Run Parameter Mapping (Used Across Branches)
`run_id -> (isColumnSplit, max_col, max_row, prah)`

| run | isColumnSplit | max_col | max_row | prah |
|---|---|---:|---:|---:|
| 1 | false | 15 | 15 | 0.60 |
| 2 | true  | 15 | 15 | 0.60 |
| 3 | true  | 15 | 20 | 0.60 |
| 4 | true  | 18 | 22 | 0.55 |
| 5 | true  | 18 | 22 | 0.58 |
| 6 | true  | 10 | 10 | 0.60 |
| 7 | true  | 16 | 20 | 0.55 |
| 8 | false | 16 | 20 | 0.55 |
| 9 | true  | 16 | 20 | 0.52 |


## 5) Important files

For each branch:
- `.../leaderboard.csv` -> run-level quality overview
- `.../<run_id>/label_category_analysis.csv` -> per-label category composition, purity, recall, f-score, feature-weight
- `.../<run_id>/bundle_overlay.svg` -> bundle visualization
- `.../<run_id>/reconstructed_matrix.csv` -> matrix reconstructed from selected mapping
- `.../<run_id>/correlation_analysis_results.csv` -> category-wise Pearson correlation + p-values

Branch roots:
- `output/experiments/bmf/animals/category/all`
- `output/experiments/bmf/animals/exemplar/all`
- `output/experiments/bmf/artifacts/category/all`
- `output/experiments/bmf/artifacts/exemplar/all`

## 6) Summary

1. We tested 4 branches x 9 parameter runs = **36 runs**.
2. We evaluated bundle quality (purity), mapping quality (distinct category match), and behavioral validity (typicality correlation).
3. There is no single run that is best on every metric in every branch.
4. For deployment-style use, we should choose per branch based on objective:
- cleaner bundles -> prioritize purity
- stronger typicality alignment -> prioritize positive significant correlation
5. Proposed balanced picks are listed in Section 6.

## 7) Preferred Run (Overall Jaccard by Run)

`*` marks the highest `overall_jaccard` value within each column (branch), i.e., preferred run for that branch.

| run | animal-category-level | animal-exemplar-level | artifacts-category-level | artifacts-exemplar-level |
|---:|---:|---:|---:|---:|
| 1 | 0.404547 | 0.031881 | 0.091536 | 0.072842 |
| 2 | 0.074764 | 0.067712 | 0.011607 | 0.006171 |
| 3 | 0.074764 | 0.070257 | 0.247902 | 0.046756 |
| 4 | 0.255938 | 0.069552 | 0.208443 | 0.096296 |
| 5 | 0.255938 | 0.069552 | 0.261591* | 0.096343* |
| 6 | 0.067937 | 0.011912 | 0.011608 | 0.004881 |
| 7 | 0.255938 | 0.070257 | 0.170976 | 0.046681 |
| 8 | 0.449952* | 0.121806* | 0.131668 | 0.072842 |
| 9 | 0.255938 | 0.014563 | 0.090626 | 0.046681 |
