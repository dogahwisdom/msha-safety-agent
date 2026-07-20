# MSHA Safety Agent

[![CI](https://github.com/dogahwisdom/msha-safety-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/dogahwisdom/msha-safety-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?logo=jupyter&logoColor=white)](https://jupyter.org/)

Tool-augmented LLM agent for **explainable mine safety risk analysis** over U.S. MSHA accident and injury data — classifier, trends, and narrative retrieval behind an auditable agent loop.

**Repository:** [github.com/dogahwisdom/msha-safety-agent](https://github.com/dogahwisdom/msha-safety-agent)

---

## What is this?

Instead of a black-box severity predictor, this system routes natural-language safety questions to three inspectable tools:

| Tool | Purpose |
|------|---------|
| **Risk classifier** | Predict injury degree from structured MSHA field codes |
| **Trend analyzer** | Counts, year-over-year changes, period comparisons |
| **Narrative retriever** | Semantic search over 240k+ incident narratives |

An LLM orchestrator (Groq, Ollama, or OpenAI) selects tools via function calling. A **zero-cost offline mode** routes by question category for reproducible paper numbers.

### Benchmark results (60 questions)

| System | Overall accuracy | Tool selection |
|--------|------------------|----------------|
| Tool-augmented agent (offline) | **93.3%** | 100% |
| Classifier baseline | 30.0% | 33% |
| Retrieval-only baseline | 30.0% | 33% |

Classifier holdout: **0.574** accuracy, **0.562** macro F1 on 48,128 test records. Full results in [docs/paper_draft.md](docs/paper_draft.md).

---

## Quick start

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
bash scripts/setup.sh
source .venv/bin/activate
make ingest && make classifier && make test
```

Reproduce the paper benchmark (no API key):

```bash
export LLM_PROVIDER=offline
make eval
```

Or use Jupyter: `make notebook` → run notebooks `01`–`06` in order.

---

## Make targets

| Command | Description |
|---------|-------------|
| `make setup` | Install dependencies (PyTorch, Jupyter, etc.) |
| `make ingest` | Download and clean MSHA data (Step 1) |
| `make classifier` | Train injury severity classifier (Step 2) |
| `make index` | Build narrative retrieval index (Step 4, ~30 min CPU) |
| `make benchmark` | Build 60-question evaluation set (Step 7) |
| `make eval` | Run benchmark + score (Steps 8–9) |
| `make test` | Unit tests (excludes slow full-index test) |
| `make notebook` | Start JupyterLab in `notebooks/` |

---

## LLM providers (no paid API required)

| Provider | Cost | Setup |
|----------|------|-------|
| **Offline tools** | Free | `LLM_PROVIDER=offline` |
| **Groq** | Free tier | `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) |
| **Ollama** | Free local | `ollama pull qwen2.5:7b` |
| OpenAI | Paid | `OPENAI_API_KEY` |

See [docs/FREE_LLM_OPTIONS.md](docs/FREE_LLM_OPTIONS.md).

```bash
cp .env.example .env
# Edit .env with your preferred provider
```

---

## Repository layout

```
msha-safety-agent/
├── src/
│   ├── data/           Ingestion, cleaning, train/test split
│   ├── tools/          Classifier, trends, retrieval
│   ├── agent/          LLM orchestrator and function calling
│   └── baselines/      Classifier and RAG baselines
├── notebooks/          Reproducible Jupyter workflow (Steps 1–6)
├── benchmark/          60 questions + reference answers
├── eval/               Benchmark runner, scoring, human-eval materials
├── docs/               Paper draft, reproduction guide, progress tracker
├── tests/              Unit tests
└── scripts/setup.sh    Resumable environment setup
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/paper_draft.md](docs/paper_draft.md) | Working paper with results |
| [docs/REPRODUCTION.md](docs/REPRODUCTION.md) | Full reproduction checklist |
| [docs/FREE_LLM_OPTIONS.md](docs/FREE_LLM_OPTIONS.md) | Free LLM setup guide |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Step-by-step implementation tracker |

---

## Data sources

- [MSHA Accident Injuries Data Set](https://catalog.data.gov/dataset/msha-accident-injuries-data-set)
- [MSHA Open Government Data Portal](https://arlweb.msha.gov/OpenGovernmentData/OGIMSHA.asp)

Raw and processed data are **not committed** — generated locally by `make ingest`.

---

## Citation

```bibtex
@software{msha_safety_agent,
  author = {Wisdom, Dogah},
  title = {MSHA Safety Agent: Tool-Augmented LLM for Mine Safety Analysis},
  year = {2026},
  url = {https://github.com/dogahwisdom/msha-safety-agent}
}
```

See also [CITATION.cff](CITATION.cff) for machine-readable metadata.

---

## License

MIT — see [LICENSE](LICENSE).
