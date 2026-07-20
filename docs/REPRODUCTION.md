# Reproduction Guide

This document helps researchers reproduce results from the MSHA Safety Agent paper draft (`docs/paper_draft.md`).

## Prerequisites

- Python 3.10+
- ~4 GB disk for raw/processed MSHA data
- ~2 GB for PyTorch and embedding models (downloaded on first use)
- OpenAI API key (**optional** — Groq free tier or Ollama work instead; see [FREE_LLM_OPTIONS.md](FREE_LLM_OPTIONS.md))

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

For CUDA PyTorch instead of CPU:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install sentence-transformers chromadb openai
```

## Reproduction paths

### Path A: Jupyter notebooks (recommended)

```bash
jupyter lab notebooks/
```

Run notebooks 01 through 06 in order. Each notebook calls the same modules as the CLI (`python -m src...`).

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

### Path C: Automated tests

```bash
pytest tests/ -v
```

Excludes slow full-index retrieval unless you run `pytest tests/test_retrieval.py -m slow`.

## Environment variables

Copy `.env.example` to `.env`. **No paid API required** for paper reproduction.

| Mode | Setup |
|------|--------|
| **Offline (paper numbers)** | `LLM_PROVIDER=offline` then Steps 8–9 |
| **Groq (free cloud, recommended)** | `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) |
| **Ollama (local)** | `ollama pull qwen2.5:7b` and `OLLAMA_MODEL=qwen2.5:7b` |
| **OpenAI (paid)** | `OPENAI_API_KEY` |

Full comparison: [FREE_LLM_OPTIONS.md](FREE_LLM_OPTIONS.md).

```bash
# Reproduce paper benchmark (offline, zero cost)
export LLM_PROVIDER=offline
python eval/run_benchmark.py
python eval/score.py
# Expect agent overall accuracy ~93.3%
```

## Expected artifacts

After a full run:

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

## Verified metrics (Step 2, stratified holdout)

These numbers come from `data/processed/classifier_evaluation.json` after running Step 2:

- Accuracy: 0.574
- Macro F1: 0.562
- Fatality (code 01) recall: 0.538

See `docs/PROGRESS.md` for full per-class recall and out-of-time split results.

## Benchmark review gate

Step 7 builds `benchmark/questions.json` before any system is evaluated on it. Review that file before running Step 8 (`eval/run_benchmark.py`).

## Human evaluation (Step 10)

Materials only: `eval/human_eval/materials.md` and `eval/human_eval/build_stimuli.py`. The repository does not include simulated participant ratings.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| PyTorch install timeout | Re-run `bash scripts/setup.sh` (resumes `.wheels/` download) |
| `ModuleNotFoundError: src` | Run notebooks from repo root or import `notebooks._path_setup` |
| Retrieval index missing | Run `python -m src.tools.run_retrieval_index` or notebook 04 |
| Agent errors | Set `GROQ_API_KEY`, run Ollama, or use `LLM_PROVIDER=offline` |
| CI vs local | GitHub Actions runs ingest + classifier train + pytest |

## Citation

Working title from the paper draft:

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data
