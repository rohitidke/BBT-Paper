# Project Overview: What We Did Step by Step

This document explains the project in plain language and in the order the work was carried out.

## 1. Project goal

The goal of this project is to study whether **unsupervised contextual bundling** can recover
meaningful internal structure inside concept categories such as animals and artifacts.

In simple terms, we start from large binary object-attribute matrices and ask:

- can we automatically group similar patterns into bundles?
- can we build a simplified **model matrix** that still represents the original data well?
- does the fit between data and model reflect **human typicality ratings**?

This project is part of the thesis work described in [thesis_abstract.md](thesis_abstract.md).

## 2. Step 1: Collect and organize the Leuven Conceptual Data

We worked with Leuven Conceptual Data for two domains:

- `animals`
- `artifacts`

The main input files are stored under:

- [data/animals](data/animals)
- [data/artifacts](data/artifacts)

These data include:

- category-level object-attribute matrices
- exemplar-level object-attribute matrices
- human typicality ratings

Why we did this:

- to test the method on more than one semantic domain
- to compare abstract category-level features with more concrete exemplar-level features

## 3. Step 2: Prepare matrices for analysis

Before running the bundling pipeline, we converted the Leuven spreadsheets into CSV matrices that
the scripts can use directly.

The key preparation scripts are:

- [scripts/dichotomize_leuven_matrix.py](scripts/dichotomize_leuven_matrix.py)
- [scripts/extract_sum_freq_normalized.py](scripts/extract_sum_freq_normalized.py)

What these scripts do:

- create dichotomized binary matrices
- create normalized feature-frequency files
- prepare the matrices used later for scoring and evaluation

Why we did this:

- the original source files are Excel sheets
- the analysis pipeline needs clean binary matrices and feature weights in CSV form

## 4. Step 3: Create several experimental data conditions

We did not evaluate only one matrix version. We created multiple conditions so we could compare
how different attribute spaces affect the results.

The project includes:

- `animals/category/all`
- `animals/exemplar/all`
- `animals/exemplar/frequency`
- `animals/exemplar/importance`
- `animals/exemplar/random`
- `artifacts/category/all`
- `artifacts/exemplar/all`
- `artifacts/exemplar/frequency`
- `artifacts/exemplar/importance`
- `artifacts/exemplar/random`

Why we did this:

- category-level and exemplar-level matrices may behave differently
- filtered exemplar matrices may remove noisy or weak attributes
- random filtering acts as a control condition

## 5. Step 4: Use Boolean Matrix Decomposition as a baseline

We used **Boolean Matrix Decomposition (BMD)** as a baseline for contextual bundling.

The baseline inputs are stored under:

- [data/bmd](data/bmd)

The baseline outputs are stored under:

- [output/experiments/bmd](output/experiments/bmd)

What BMD gives us:

- a `data_matrix.csv`
- a `model_matrix.csv`
- an `overall_jaccard.txt`
- correlation outputs against typicality ratings

Why we did this:

- BMD is the classical reference point for contextual bundling
- it lets us compare the newer unsupervised pipeline against a known baseline

## 6. Step 5: Run the image-processing Boolean Matrix Factorization pipeline

The main experimental pipeline in this repo is the **image-processing / OTSU-based Boolean Matrix
Factorization (BMF)** workflow.

Relevant code and MATLAB files:

- [matlab/run.m](matlab/run.m)
- [matlab/deleni.m](matlab/deleni.m)
- [scripts/extract_animals_by_label.py](scripts/extract_animals_by_label.py)
- [scripts/visualize_bundles.py](scripts/visualize_bundles.py)
- [scripts/reconstruct_matrix_from_best_mapping.py](scripts/reconstruct_matrix_from_best_mapping.py)
- [scripts/correlation_analysis.py](scripts/correlation_analysis.py)

What happened in this step:

1. MATLAB was used to generate label assignments (`label_membership_cells.csv`) for each run.
2. Python scripts converted those labels into category-label analyses and summary files.
3. We visualized detected bundles with overlay figures.
4. We reconstructed a model matrix from the selected label-category mapping.
5. We correlated model fit with human typicality ratings.

Why we did this:

- BMD is limited for larger exemplar-level matrices
- the BMF pipeline is a scalable unsupervised alternative
- it allows run-wise parameter exploration

## 7. Step 6: Test multiple parameter settings

For the BMF workflow, we ran multiple parameter settings instead of trusting a single run.

The run mapping used in the project is documented in [README_RESULTS.md](README_RESULTS.md).

Across the main BMF branches, we evaluated runs `1..9` with different settings for:

- `isColumnSplit`
- `max_col`
- `max_row`
- `prah`

Why we did this:

- different parameter settings produce different bundle structures
- some runs reconstruct the matrix better
- some runs align better with human typicality ratings

## 8. Step 7: Evaluate structural quality

After each run, we measured how good the resulting bundle solution was structurally.

Important outputs include:

- `leaderboard.csv`
- `label_category_analysis.csv`
- `summary.txt`
- `summary.json`
- `model_matrix_stats.txt`

Important evaluation criteria:

- bundle purity
- weighted purity
- distinct category-label matching accuracy
- overall Jaccard goodness of fit

Why we did this:

- a good run should not only produce bundles
- the bundles should also be interpretable and close to the original matrix structure

## 9. Step 8: Evaluate behavioral validity with typicality

The key psychological test in this project is whether object-level fit values correlate with
human typicality judgments.

This analysis is produced by:

- [scripts/correlation_analysis.py](scripts/correlation_analysis.py)
- [scripts/correlation_analysis_bmd.py](scripts/correlation_analysis_bmd.py)
- [scripts/correlation_analysis_bmd_from_csv.py](scripts/correlation_analysis_bmd_from_csv.py)

Main outputs:

- `correlation_analysis_results.csv`
- `typicality_similarity_enriched.csv`

Why we did this:

- matrix reconstruction quality alone is not enough
- we want to know whether the model reflects graded category structure that humans also perceive

## 10. Step 9: Select preferred runs

After comparing runs, we selected preferred runs for each branch.

The current preferred locations are documented in
[README_OUTPUT_STRUCTURE.md](README_OUTPUT_STRUCTURE.md).

Current preferred branches include:

- `animals/category/all -> preferred/8`
- `animals/exemplar/all -> preferred/8`
- `animals/exemplar/frequency -> preferred/1`
- `animals/exemplar/importance -> preferred/4`
- `animals/exemplar/random -> preferred/4`
- `artifacts/category/all -> preferred/5`
- `artifacts/exemplar/all -> preferred/5`
- `artifacts/exemplar/frequency -> preferred/1`
- `artifacts/exemplar/importance -> preferred/4`
- `artifacts/exemplar/random -> preferred/9`

Why we did this:

- no single run is best in every condition
- preferred runs make the final comparison more stable and easier to interpret

## 11. Step 10: Organize outputs for comparison

The final outputs were organized into a consistent folder structure:

- [output/experiments/bmf](output/experiments/bmf)
- [output/experiments/bmd](output/experiments/bmd)
- [output/figures](output/figures)

This makes it possible to compare:

- BMD vs BMF
- animals vs artifacts
- category vs exemplar
- unfiltered vs frequency / importance / random filtered data

## 12. What the project has shown so far

At this stage, the project suggests the following:

- unsupervised contextual bundling can work, but success depends strongly on model-matrix quality
- category-level results are currently more stable than exemplar-level results
- animals show the clearest positive results, especially at category level
- filtered exemplar conditions are useful for testing whether removing weaker attributes helps
- structural quality and behavioral validity do not always peak in the same run

## 13. Most important files to read next

If someone wants to understand the repo quickly, these are the best starting points:

- [README.md](README.md)
- [README_RESULTS.md](README_RESULTS.md)
- [README_OUTPUT_STRUCTURE.md](README_OUTPUT_STRUCTURE.md)
- [thesis_abstract.md](thesis_abstract.md)

For branch-specific execution guides:

- [README_ANIMALS_EXEMPLAR.md](README_ANIMALS_EXEMPLAR.md)
- [README_ARTIFACTS.md](README_ARTIFACTS.md)
- [README_ARTIFACTS_EXEMPLAR.md](README_ARTIFACTS_EXEMPLAR.md)
- [README_DENOISED_ALL_PREFERRED.md](README_DENOISED_ALL_PREFERRED.md)

## 14. Short summary

This project built a full workflow for unsupervised contextual bundling:

1. prepare Leuven object-attribute data
2. create binary matrices and feature weights
3. run baseline BMD analyses
4. run unsupervised BMF experiments across many parameter settings
5. evaluate bundle quality and matrix fit
6. test alignment with human typicality ratings
7. select preferred runs for each branch

In short, the repo is not just a collection of scripts. It is a complete experimental pipeline for
studying whether unsupervised bundle induction can recover psychologically meaningful
intra-categorical structure.
