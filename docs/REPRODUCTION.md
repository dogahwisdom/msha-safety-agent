# Reproduction Guide

How to reproduce results from the MSHA Safety Agent paper ([paper_draft.md](paper_draft.md)).

## Prerequisites

- Python 3.10+
- ~4 GB disk for raw/processed MSHA data
- ~2 GB for PyTorch and embedding models (downloaded on first use)
- **Groq API key** for the primary live LLM benchmark (free tier at [console.groq.com](https://console.groq.com))
- Offline routing ablation requires no API key

## One-command setup

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
bash scripts/setup.sh
source .venv/bin/activate
cp .env.example .env
# Add GROQ_API_KEY to .env for primary benchmark
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

Or use Make: `make ingest`, `make classifier`, `make index`, `make benchmark`, `make eval-groq`.

### Path C: Automated tests

```bash
pytest tests/ -v -m "not slow"
```

Run `pytest tests/test_retrieval.py -m slow` for the full-index retrieval check.

## LLM providers

### Groq (primary live benchmark)

Free tier at [console.groq.com](https://console.groq.com) (no credit card). Uses Llama 3.3 70B via an OpenAI-compatible API. This is the **primary reported result** in the paper: a live LLM that plans and calls tools.

```bash
# .env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq

make eval-groq
```

Limits: ~30 requests/min, ~1,000 requests/day on 70B. One full 60-question run uses 180 LLM calls (agent + two baselines).

### Offline deterministic router (ablation only)

Category-based routing with no LLM calls. This is **not** the paper's primary claim about agentic LLM orchestration. It measures a zero-cost routing ceiling when category metadata is available.

```bash
make eval-offline
```

### Ollama (local, supplementary)

```bash
ollama pull qwen2.5:7b
export OLLAMA_MODEL=qwen2.5:7b
export LLM_PROVIDER=ollama
```

Prior supplementary runs with `qwen2.5:7b` scored poorly on trend questions. Use Groq 70B for the primary live comparison.

### OpenAI (paid)

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL=gpt-4o-mini`.

### Provider priority (`LLM_PROVIDER=auto`, default)

1. `OPENAI_API_KEY` → OpenAI
2. `GROQ_API_KEY` → Groq
3. Ollama on `localhost:11434` → Ollama
4. None → offline deterministic router

Force a mode: `LLM_PROVIDER=offline|groq|ollama|openai`

## Expected artifacts

| Artifact | Location |
|----------|----------|
| Cleaned data | `data/processed/accidents_clean.csv` |
| Classifier model | `data/processed/injury_risk_classifier.joblib` |
| Classifier metrics | `data/processed/classifier_evaluation.json` |
| Retrieval index | `data/processed/chroma_narratives/` |
| Benchmark | `benchmark/questions.json`, `benchmark/reference_answers.json` |
| Primary live runs | `eval/results/benchmark_runs_groq_fixed.json` |
| Offline ablation runs | `eval/results/benchmark_runs_offline_fixed.json` |
| Scores | `eval/results/scores_groq_fixed.json` (derived from output filename) |

None of these are committed (see `.gitignore`).

## Reference metrics

### Classifier (stratified holdout, n=48,128)

| Metric | Value |
|--------|-------|
| Accuracy | 0.574 |
| Macro F1 | 0.562 |
| Fatality (01) recall | 0.538 |

Out-of-time split (train 2000–2020, test 2021+): accuracy 0.553, macro F1 0.559, fatality recall 0.456. Weak recall on codes 04, 09, and 10. Full per-class tables are in `classifier_evaluation.json` after `make classifier`.

**Leakage check:** `DAYS_LOST` and `DAYS_RESTRICT` are not in `CLASSIFIER_FEATURE_COLUMNS`; they are listed in `CLASSIFIER_LEAKAGE_COLUMNS` in `src/data/config.py`.

### Primary benchmark (Groq llama-3.3-70b, 60 questions, corrected baselines)

Run `make eval-groq` with `GROQ_API_KEY` set. Results are written to `eval/results/benchmark_runs_groq_fixed.json`. Use `bash scripts/run_groq_benchmark.sh` for resumable checkpointed runs.

All three systems attempt all 60 questions. The classifier baseline always calls `classify_injury_risk` (with inferred defaults when field codes are missing). The RAG baseline always retrieves narratives and passes them to the LLM in one shot.

| System | Classification | Trend | Case grounded | Overall | Tool selection / use |
|--------|----------------|-------|---------------|---------|---------------------|
| Tool-augmented agent (Groq) | 85.0% | 5.0% | 25.0% | **38.3%** | 60.0% |
| Classifier baseline | 90.0% | 0.0% | 0.0% | 30.0% | 100% |
| RAG baseline | 0.0% | 0.0% | 85.0% | 28.3% | 98.3% |

Mean latency: agent 126 s, classifier 0.19 s, RAG 256 s. Total tokens: agent 69,650, RAG 38,252.

### Offline routing ablation (deterministic, no LLM)

| System | Classification | Trend | Case grounded | Overall | Tool use |
|--------|----------------|-------|---------------|---------|----------|
| Offline router | 90.0% | 100.0% | 90.0% | 93.3% | 100% |
| Classifier baseline | 90.0% | 0.0% | 0.0% | 30.0% | 100% |
| RAG baseline (no LLM) | 0.0% | 0.0% | 90.0% | 30.0% | 100% |

The 30% overall scores for single-tool baselines reflect failure on out-of-strength questions after **attempting** every question, not structural exclusion. Mean latency: offline router 0.31 s, classifier 0.22 s, RAG 0.03 s.

### Benchmark failure analysis (offline router)

| System | Failures | Cause |
|--------|----------|-------|
| Offline router | 4 / 60 | Classifier errors (2), retrieval rank (2) |
| Classifier baseline | 42 / 60 | Wrong tool for trend/case questions (expected) |
| RAG baseline (no LLM) | 42 / 60 | Retrieval-only cannot answer counts or degree codes |

## Human evaluation

Protocol and stimulus builder: `eval/human_eval/materials.md`, `eval/human_eval/build_stimuli.py`.

**Primary Groq benchmark is complete.** Participant collection may proceed after reviewing `docs/paper_draft.md` Section 6.2.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| PyTorch install timeout | Re-run `bash scripts/setup.sh` |
| `ModuleNotFoundError: src` | Run from repo root or import `notebooks._path_setup` |
| Retrieval index missing | `make index` or notebook 04 |
| `LLM_PROVIDER=groq but GROQ_API_KEY is not set` | Add key to `.env` |
| Groq 429 rate limit | Wait and re-run; or split runs by system |
| CI vs local | GitHub Actions runs ingest + classifier train + pytest |

## Citation

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data

See [CITATION.cff](../CITATION.cff) for BibTeX-compatible metadata.
