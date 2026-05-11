# BMD Artifacts Exemplar Correlation (frequency / importance / random)

This guide runs correlation analysis for artifacts exemplar branches using:
- `scripts/correlation_analysis_bmd.py`

It compares:
- data matrix JSON from `data/bmd/data_matrix/`
- model matrix JSON from `data/bmd/model_matrix/`

and writes outputs to:
- `output/experiments/bmd/artifacts/exemplar/<branch>/`

## 1. Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas scipy
```

## 2. Inputs

Typicality file used automatically for artifacts:
- `data/artifacts/typicality_ratings.csv`

Data JSON files:
- `data/bmd/data_matrix/artifacts_frequency.json`
- `data/bmd/data_matrix/artifacts_importance.json`
- `data/bmd/data_matrix/artifacts_random.json`

Model JSON files (current examples):
- `data/bmd/model_matrix/artifacts_frequency_5.json`
- `data/bmd/model_matrix/artifacts_importance_5.json`
- `data/bmd/model_matrix/artifacts_random_5.json`

If you want run-1 model matrices instead, use:
- `artifacts_frequency_1.json`
- `artifacts_importance_1.json`
- `artifacts_random_1.json`

## 3. Run Per Branch

### 3.1 frequency

```bash
./.venv/bin/python scripts/correlation_analysis_bmd.py \
  --data-matrix data/bmd/data_matrix/artifacts_frequency.json \
  --model-matrix data/bmd/model_matrix/artifacts_frequency_5.json
```

### 3.2 importance

```bash
./.venv/bin/python scripts/correlation_analysis_bmd.py \
  --data-matrix data/bmd/data_matrix/artifacts_importance.json \
  --model-matrix data/bmd/model_matrix/artifacts_importance_5.json
```

### 3.3 random

```bash
./.venv/bin/python scripts/correlation_analysis_bmd.py \
  --data-matrix data/bmd/data_matrix/artifacts_random.json \
  --model-matrix data/bmd/model_matrix/artifacts_random_5.json
```

## 4. Run All Three Branches (zsh-compatible)

```zsh
for branch in frequency importance random; do
  ./.venv/bin/python scripts/correlation_analysis_bmd.py \
    --data-matrix "data/bmd/data_matrix/artifacts_${branch}.json" \
    --model-matrix "data/bmd/model_matrix/artifacts_${branch}_5.json"
done
```

To run with `_1` model files instead of `_5`, change:
- `artifacts_${branch}_5.json` -> `artifacts_${branch}_1.json`

## 5. Outputs

For each branch, outputs are created in:
- `output/experiments/bmd/artifacts/exemplar/<branch>/`

Files produced:
- `data_matrix.csv`
- `model_matrix.csv`
- `overall_jaccard.txt`
- `typicality_similarity_enriched.csv`
- `correlation_analysis_results.csv`
