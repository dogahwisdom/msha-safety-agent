# MSHA Safety Agent

Research codebase for a tool-augmented LLM agent that answers natural-language mine safety questions over U.S. Mine Safety and Health Administration (MSHA) accident and injury data.

Instead of only predicting injury severity with a black-box classifier, the system uses an LLM to decide when to call three inspectable tools (a risk classifier, a trend analyzer, and a narrative retriever), then produces answers that can be audited and rated by domain experts.

**Paper draft (source of truth):** [docs/paper_draft.md](docs/paper_draft.md)

**Implementation progress:** [PROGRESS.md](PROGRESS.md)

**Reproduction guide:** [docs/REPRODUCTION.md](docs/REPRODUCTION.md)

| Step | Component | Status |
|------|-----------|--------|
| 1 | Data acquisition and cleaning | Done |
| 2 | Classifier tool | Done |
| 3 | Trend analysis tool | Done |
| 4 | Narrative retrieval tool | Done (index build required locally) |
| 5 | Orchestrator (LLM) | Done (requires `OPENAI_API_KEY`) |
| 6 | Baselines | Done |
| 7 | Benchmark construction | Done (review before Step 8 runs) |
| 8 | System comparison runs | Ready (requires API key + benchmark review) |
| 9 | Scoring | Done |
| 10 | Human evaluation materials | Done (materials only) |

Results, Abstract, and Introduction in the paper draft are revised only after experiments are complete.

---

## Quick start (researchers)

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
bash scripts/setup.sh          # installs PyTorch, Jupyter, all deps
source .venv/bin/activate
jupyter lab notebooks/         # run notebooks 01–06 in order
```

Or use the CLI path documented in [docs/REPRODUCTION.md](docs/REPRODUCTION.md).

---

## Project layout

| Path | Purpose |
|------|---------|
| `notebooks/` | **Primary reproduction path** — one notebook per pipeline stage |
| `scripts/setup.sh` | Resumable install (PyTorch wheel cache in `.wheels/`) |
| `data/raw/` | Downloaded MSHA files (not committed) |
| `data/processed/` | Cleaned data, models, vector index (not committed) |
| `src/data/` | Ingestion and cleaning pipeline |
| `src/tools/` | Classifier, trend, and retrieval tools |
| `src/agent/` | Orchestrator: system prompt, function calling, agent loop |
| `src/baselines/` | Plain classifier baseline and single-shot RAG baseline |
| `benchmark/` | Question set and reference answers |
| `eval/` | Scoring, logging, and human evaluation materials |
| `docs/` | Paper draft and reproduction guide |
| `tests/` | Unit tests mirroring notebook checks |

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
bash scripts/setup.sh
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` for agent and RAG baseline notebooks (Steps 5–8).

**Dependencies include:** PyTorch (CPU), sentence-transformers, chromadb, OpenAI SDK, JupyterLab, pandas, scikit-learn.

---

## Data pipeline (Step 1)

```bash
python -m src.data.ingest
```

Or run [notebooks/01_data_ingestion.ipynb](notebooks/01_data_ingestion.ipynb).

**Verified counts (2026-07-19):** 273,614 raw accident rows, 240,640 after cleaning, 192,512 train / 48,128 test.

---

## Tools and agent

| Step | CLI | Notebook |
|------|-----|----------|
| Classifier | `python -m src.tools.run_classifier` | `02_classifier_tool.ipynb` |
| Trends | `pytest tests/test_trends.py` | `03_trend_analysis.ipynb` |
| Retrieval | `python -m src.tools.run_retrieval_index` | `04_narrative_retrieval.ipynb` |
| Agent | `python -m src.agent.run_agent "..."` | `05_agent_and_baselines.ipynb` |
| Benchmark | `python benchmark/build_benchmark.py` | `06_benchmark_evaluation.ipynb` |

---

## Testing

```bash
pytest tests/ -v
pytest tests/ -m "not slow"   # skip full retrieval index test
```

---

## Implementation order

From Section 6 of the paper draft. See [PROGRESS.md](PROGRESS.md) for verified metrics and notes.

---

## Data sources

- [MSHA Accident Injuries Data Set](https://catalog.data.gov/dataset/msha-accident-injuries-data-set)
- [MSHA Open Government Data Portal](https://arlweb.msha.gov/OpenGovernmentData/OGIMSHA.asp)

---

## Citation

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data
