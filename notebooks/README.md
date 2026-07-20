# Notebooks

Interactive reproduction of the ten-step pipeline from `docs/paper_draft.md`.

Each notebook imports logic from `src/` (no duplicated pipeline code). Run notebooks in order for a full reproduction.

| Notebook | Step | What it does |
|----------|------|--------------|
| [01_data_ingestion.ipynb](01_data_ingestion.ipynb) | 1 | Download, clean, join, split MSHA data |
| [02_classifier_tool.ipynb](02_classifier_tool.ipynb) | 2 | Train and evaluate injury severity classifier |
| [03_trend_analysis.ipynb](03_trend_analysis.ipynb) | 3 | Trend queries and partial-year handling |
| [04_narrative_retrieval.ipynb](04_narrative_retrieval.ipynb) | 4 | Build index and hand-check retrieval |
| [05_agent_and_baselines.ipynb](05_agent_and_baselines.ipynb) | 5–6 | Agent orchestrator and baselines (LLM key required) |
| [06_benchmark_evaluation.ipynb](06_benchmark_evaluation.ipynb) | 7–9 | Benchmark, runs, scoring |

Human evaluation protocol: `eval/human_eval/` (survey materials and stimulus builder).

## Quick start

```bash
bash scripts/setup.sh
source .venv/bin/activate
jupyter lab notebooks/
```

Select kernel **MSHA Safety Agent** (registered by `scripts/setup.sh`).

## Notes for researchers

- Raw and processed data are not committed. Notebook 01 downloads MSHA open data on first run.
- Step 4 index build over ~240k narratives takes 15–30 minutes on CPU.
- Steps 5–8: configure Groq, Ollama, OpenAI, or `LLM_PROVIDER=offline` — see [docs/REPRODUCTION.md](../docs/REPRODUCTION.md)
- Unit tests in `tests/` mirror notebook checks: `pytest tests/ -v`

See [docs/REPRODUCTION.md](../docs/REPRODUCTION.md) for the full checklist.
