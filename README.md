# MSHA Safety Agent

Research codebase for a tool-augmented LLM agent that answers natural-language mine safety questions over U.S. Mine Safety and Health Administration (MSHA) accident and injury data.

Instead of only predicting injury severity with a black-box classifier, the system uses an LLM to decide when to call three inspectable tools (a risk classifier, a trend analyzer, and a narrative retriever), then produces answers that can be audited and rated by domain experts.

**Paper draft (source of truth):** [docs/paper_draft.md](docs/paper_draft.md)

**Implementation progress:** [PROGRESS.md](PROGRESS.md)

| Step | Component | Status |
|------|-----------|--------|
| 1 | Data acquisition and cleaning | Done |
| 2 | Classifier tool | Not started |
| 3 | Trend analysis tool | Not started |
| 4 | Narrative retrieval tool | Not started |
| 5 | Orchestrator (LLM) | Waiting on provider choice |
| 6 | Baselines | Not started |
| 7 | Benchmark construction | Not started |
| 8 | System comparison runs | Not started |
| 9 | Scoring | Not started |
| 10 | Human evaluation materials | Not started |

Results, Abstract, and Introduction in the paper draft are revised only after experiments are complete.

---

## Project layout

| Path | Purpose |
|------|---------|
| `data/raw/` | Downloaded MSHA files (not committed) |
| `data/processed/` | Cleaned and split data (not committed) |
| `src/data/` | Ingestion and cleaning pipeline |
| `src/tools/` | Classifier, trend, and retrieval tools (independently testable) |
| `src/agent/` | Orchestrator: system prompt, function calling, agent loop |
| `src/baselines/` | Plain classifier baseline and single-shot RAG baseline |
| `benchmark/` | Question set and reference answers (written before any system is run) |
| `eval/` | Scoring, logging, and Explanation Satisfaction Scale materials |
| `notebooks/` | Exploratory analysis |
| `docs/` | Paper draft and later revisions |
| `tests/` | Unit and integration tests for each module |

---

## Setup

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` when you configure an LLM provider for Step 5. Do not commit `.env`.

---

## Data pipeline (Step 1)

Download, clean, join, and split MSHA data:

```bash
python -m src.data.ingest
```

This pulls the [Accident Injuries](https://catalog.data.gov/dataset/msha-accident-injuries-data-set) and [Mines](https://arlweb.msha.gov/OpenGovernmentData/OGIMSHA.asp) datasets from MSHA's open data portal, applies documented filtering rules, and writes:

| Output | Description |
|--------|-------------|
| `data/processed/accidents_clean.csv` | Cleaned accidents joined to mine context |
| `data/processed/mines_clean.csv` | Mine identification subset |
| `data/processed/accidents_train.csv` | 80% stratified training split |
| `data/processed/accidents_test.csv` | 20% stratified held-out test split |
| `data/processed/ingestion_summary.json` | Row counts, class distribution, cleaning log |

Re-download raw files with `--force-download` if needed.

**Verified counts (2026-07-19):** 273,614 raw accident rows, 240,640 after cleaning, 192,512 train / 48,128 test. See [PROGRESS.md](PROGRESS.md) for filtering decisions, external review follow-up, and class distribution.

---

## Testing

```bash
pytest tests/ -v
```

Tests require raw data under `data/raw/`. Run `python -m src.data.ingest` first if you have not downloaded the datasets.

---

## Implementation order

From Section 6 of the paper draft. Steps must be completed in order; each module is tested before the next step begins.

1. Acquire and clean the MSHA data.
2. Build and test the classifier tool standalone.
3. Build and test the trend analysis tool standalone.
4. Build and hand-check the narrative retrieval index.
5. Wire up the orchestrator with function calling and full logging (requires LLM provider).
6. Build both baselines.
7. Write benchmark questions and reference answers before running any system on them.
8. Run all three systems under identical conditions and log everything.
9. Score accuracy against reference answers.
10. Prepare human evaluation materials (Explanation Satisfaction Scale).
11. Fill in Results and revise Abstract/Introduction with measured numbers.

---

## Data sources

- [MSHA Accident Injuries Data Set](https://catalog.data.gov/dataset/msha-accident-injuries-data-set)
- [MSHA Open Government Data Portal](https://arlweb.msha.gov/OpenGovernmentData/OGIMSHA.asp)
- Field definitions: [Accidents definition file](https://arlweb.msha.gov/OpenGovernmentData/DataSets/Accidents_Definition_File.txt)

Raw and processed data files are excluded from git via `.gitignore`. Clone this repo and run the ingest script to reproduce the processed files locally.

---

## Citation

Working title from the paper draft:

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data
