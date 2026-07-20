.PHONY: setup ingest test test-all notebook classifier index benchmark eval paper help

help:
	@echo "MSHA Safety Agent — common targets"
	@echo "  make setup      Install dependencies (PyTorch, Jupyter, etc.)"
	@echo "  make ingest     Run data pipeline (Step 1)"
	@echo "  make test       Run unit tests (excludes slow retrieval index test)"
	@echo "  make classifier Train classifier (Step 2)"
	@echo "  make index      Build narrative retrieval index (Step 4)"
	@echo "  make benchmark  Build benchmark questions (Step 7)"
	@echo "  make eval       Run benchmark + score (Steps 8–9, respects LLM_PROVIDER)"
	@echo "  make paper      Build LaTeX manuscript PDF + arXiv tarball"
	@echo "  make notebook   Start JupyterLab in notebooks/"

setup:
	bash scripts/setup.sh

ingest:
	.venv/bin/python -m src.data.ingest

test:
	.venv/bin/pytest tests/ -v -m "not slow"

test-all:
	.venv/bin/pytest tests/ -v

classifier:
	.venv/bin/python -m src.tools.run_classifier

index:
	.venv/bin/python -m src.tools.run_retrieval_index

benchmark:
	.venv/bin/python benchmark/build_benchmark.py

eval:
	.venv/bin/python eval/run_benchmark.py
	.venv/bin/python eval/score.py

notebook:
	.venv/bin/jupyter lab notebooks/

paper:
	bash scripts/build_paper.sh
