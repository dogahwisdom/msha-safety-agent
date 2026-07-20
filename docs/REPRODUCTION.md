# Reproduction Guide

How to reproduce results from the MSHA Safety Agent paper ([paper_draft.md](paper_draft.md)).

## Prerequisites

- Python 3.10+
- ~4 GB disk for raw/processed MSHA data
- ~2 GB for PyTorch and embedding models (downloaded on first use)
- LLM API key **optional** (offline mode reproduces paper benchmark numbers)

## One-command setup

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
bash scripts/setup.sh
source .venv/bin/activate
```

`scripts/setup.sh` creates `.venv`, installs dependencies (including PyTorch CPU), registers the Jupyter kernel, and copies `.env.example` to `.env`.

If PyTorch download fails on slow networks, re-run the script; the wheel download in `.wheels/` is resumable.

### GPU (optional)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install sentence-transformers chromadb openai
```

## Reproduction paths

### Path A: Jupyter notebooks (recommended)

```bash
jupyter lab notebooks/
```

Run notebooks 01 through 06 in order. Each notebook calls the same modules as the CLI.

### Path B: Command line

| Step | Command |
|------|---------|
| 1 | `python -m src.data.ingest` |
| 2 | `python -m src.tools.run_classifier` |
| 3 | `pytest tests/test_trends.py -v` |
| 4 | `python -m src.tools.run_retrieval_index` |
| 5 | `python -m src.agent.run_agent "How many fatalities in 2015?"` |
| 7 | `python benchmark/build_benchmark.py` |
| 8 | `python eval/run_benchmark.py` |
| 9 | `python eval/score.py` |

Or use Make: `make ingest`, `make classifier`, `make index`, `make benchmark`, `make eval`.

### Path C: Automated tests

```bash
pytest tests/ -v -m "not slow"
```

Run `pytest tests/test_retrieval.py -m slow` for the full-index retrieval check.

## LLM providers

No paid API is required to reproduce the primary benchmark (93.3% offline agent accuracy).

### Offline tools (paper benchmark)

Deterministic category-based routing — no LLM calls:

```bash
export LLM_PROVIDER=offline
python eval/run_benchmark.py
python eval/score.py
```

### Groq (recommended for live LLM runs)

Free tier at [console.groq.com](https://console.groq.com) (no credit card). Uses Llama 3.3 70B via an OpenAI-compatible API.

```bash
# .env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
```

Limits: ~30 requests/min, ~1,000 requests/day on 70B — sufficient for one 60-question benchmark.

### Ollama (local)

```bash
ollama pull qwen2.5:7b
export OLLAMA_MODEL=qwen2.5:7b
export LLM_PROVIDER=ollama
```

Supplementary runs with `qwen2.5:7b` scored 53.3% overall (0% on trend questions). Prefer Groq 70B or offline routing for reliable results.

### OpenAI (paid)

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL=gpt-4o-mini`.

### Provider priority (`LLM_PROVIDER=auto`, default)

1. `OPENAI_API_KEY` → OpenAI
2. `GROQ_API_KEY` → Groq
3. Ollama on `localhost:11434` → Ollama
4. None → offline tool routing

Force a mode: `LLM_PROVIDER=offline|groq|ollama|openai`

## Expected artifacts

| Artifact | Location |
|----------|----------|
| Cleaned data | `data/processed/accidents_clean.csv` |
| Classifier model | `data/processed/injury_risk_classifier.joblib` |
| Classifier metrics | `data/processed/classifier_evaluation.json` |
| Retrieval index | `data/processed/chroma_narratives/` |
| Benchmark | `benchmark/questions.json`, `benchmark/reference_answers.json` |
| System runs | `eval/results/benchmark_runs.json` |
| Scores | `eval/results/scores.json` |

None of these are committed (see `.gitignore`).

## Reference metrics

### Classifier (stratified holdout, n=48,128)

| Metric | Value |
|--------|-------|
| Accuracy | 0.574 |
| Macro F1 | 0.562 |
| Fatality (01) recall | 0.538 |

Out-of-time split (train 2000–2020, test 2021+): accuracy 0.553, macro F1 0.559, fatality recall 0.456. Weak recall on codes 04, 09, and 10. Full per-class tables are in `classifier_evaluation.json` after `make classifier`.

### Benchmark (offline agent, 60 questions)

| System | Overall | Tool selection |
|--------|---------|----------------|
| Tool-augmented agent | 93.3% | 100% |
| Classifier baseline | 30.0% | 33% |
| Retrieval-only baseline | 30.0% | 33% |

Single-tool baselines cover one question category each (20/60), so 30% overall is expected.

### Benchmark failure analysis

| System | Failures | Cause |
|--------|----------|-------|
| Agent (offline) | 4 / 60 | Classifier errors (2), retrieval rank (2) |
| Classifier baseline | 42 / 60 | Out-of-domain questions by design |
| Retrieval baseline | 42 / 60 | Out-of-domain questions by design |

**Agent failures:**

- **CLS-03, CLS-14:** Classifier predicted degree code `03`; routing was correct (macro F1: 0.562).
- **CASE-14, CASE-15:** Semantic retrieval did not rank the reference document in the top five results.

Trend category: 100% (20/20) after filter normalization for fatality counts and hyphenated degree-code forms.

## Human evaluation

Protocol and stimulus builder: `eval/human_eval/materials.md`, `eval/human_eval/build_stimuli.py`.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| PyTorch install timeout | Re-run `bash scripts/setup.sh` |
| `ModuleNotFoundError: src` | Run from repo root or import `notebooks._path_setup` |
| Retrieval index missing | `make index` or notebook 04 |
| Agent errors | Set `GROQ_API_KEY`, run Ollama, or `LLM_PROVIDER=offline` |
| CI vs local | GitHub Actions runs ingest + classifier train + pytest |

## Citation

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data

See [CITATION.cff](../CITATION.cff) for BibTeX-compatible metadata.
