# MSHA Safety Agent

Research codebase for a **tool-augmented LLM agent** that answers natural-language mine safety questions over U.S. Mine Safety and Health Administration (MSHA) accident and injury data.

Instead of only predicting injury severity with a black-box classifier, the system uses an LLM to decide when to call three inspectable tools — a risk classifier, a trend analyzer, and a narrative retriever — then produces answers that can be audited and rated by domain experts.

**Paper draft (source of truth):** [docs/paper_draft.md](docs/paper_draft.md)

> Status: scaffolding only. Implementation follows the ordered checklist below. Results, Abstract, and Introduction are revised only after experiments are complete.

---

## Project layout

| Path | Purpose |
|------|---------|
| `data/raw/` | Downloaded MSHA files (untouched; not committed) |
| `data/processed/` | Cleaned and split data (not committed) |
| `src/data/` | Ingestion and cleaning scripts |
| `src/tools/` | Classifier, trend, and retrieval tools (independently testable) |
| `src/agent/` | Orchestrator: system prompt, function calling, agent loop |
| `src/baselines/` | Plain classifier baseline and single-shot RAG baseline |
| `benchmark/` | Question set and reference answers (written before any system is run) |
| `eval/` | Scoring, logging, and Explanation Satisfaction Scale materials |
| `notebooks/` | Exploratory analysis |
| `docs/` | Paper draft and later revisions |

---

## Setup

```bash
git clone https://github.com/dogahwisdom/msha-safety-agent.git
cd msha-safety-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The LLM provider SDK is not pinned yet. Confirm the provider (OpenAI, Anthropic, Gemini, Azure, Ollama, etc.) before adding it to `requirements.txt`.

---

## Implementation order

From Section 6 of the paper draft. Do these in order.

1. **Acquire and clean the MSHA data** — download Accident Injuries and Mine Identification; clean, document exclusions, stratified train/test split.
2. **Build and test the classifier tool standalone** — random forest or gradient boosted tree, evaluated before any LLM wiring.
3. **Build and test the trend analysis tool standalone** — rates, counts, and changes over time, checked against hand-verified examples.
4. **Build and hand-check the narrative retrieval index** — chunk, embed, store in a vector DB; verify retrieval by hand before agent integration.
5. **Wire up the orchestrator with function calling and full logging** — system prompt, native function calling, logs of every tool call and intermediate step.
6. **Build both baselines** — plain classifier and single-shot RAG, ready before any comparison run.
7. **Write the benchmark questions and reference answers before running anything on them** — ≥60 questions across classification, trend, and case-grounded categories.
8. **Run all three systems under identical conditions and log everything** — answers, tool calls, latency, and token usage per query.
9. **Score accuracy against the reference answers** — including a consistency check on scoring.
10. **Run the human evaluation last, blinded and randomized** — Hoffman et al. Explanation Satisfaction Scale.
11. **Only then fill in Results and revise Abstract/Introduction** — replace expected outcomes with measured numbers.

---

## Citation

Working title from the paper draft:

> Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data

Primary data: [MSHA Accident Injuries Data Set](https://catalog.data.gov/dataset/msha-accident-injuries-data-set).
