.PHONY: setup ingest test test-all notebook classifier index benchmark eval eval-offline eval-groq human-eval-stimuli human-eval-oauth human-eval-forms human-eval-forms-all human-eval-forms-extended human-eval-forms-refresh human-eval-portal significance-test paper help

help:
	@echo "MSHA Safety Agent — common targets"
	@echo "  make setup      Install dependencies (PyTorch, Jupyter, etc.)"
	@echo "  make ingest     Run data pipeline (Step 1)"
	@echo "  make test       Run unit tests (excludes slow retrieval index test)"
	@echo "  make classifier Train classifier (Step 2)"
	@echo "  make index      Build narrative retrieval index (Step 4)"
	@echo "  make benchmark  Build benchmark questions (Step 7)"
	@echo "  make eval-groq   Resumable Groq benchmark (Steps 8–9, primary result)"
	@echo "  make human-eval-stimuli  Build blinded ESS survey packets (Step 10)"
	@echo "  make human-eval-oauth   Authorize Google Forms API (one-time OAuth)"
	@echo "  make human-eval-forms   Create Google Form(s) and participant portal"
	@echo "  make human-eval-forms-all Generate P002-P010 forms and refresh portal"
	@echo "  make human-eval-forms-extended Generate P011-P020 forms and refresh portal"
	@echo "  make human-eval-portal  Rebuild participant portal from form_links.csv"
	@echo "  make significance-test McNemar test on Groq benchmark (n=60)"
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

eval-offline:
	LLM_PROVIDER=offline BENCHMARK_OUTPUT=benchmark_runs_offline.json \
		.venv/bin/python eval/run_benchmark.py
	BENCHMARK_OUTPUT=benchmark_runs_offline.json \
		.venv/bin/python eval/score.py

eval-groq:
	GROQ_BENCHMARK_DELAY_S=2.5 BENCHMARK_CHECKPOINT=eval/results/benchmark_runs_groq_partial.jsonl \
		bash scripts/run_groq_benchmark.sh

human-eval-stimuli:
	.venv/bin/python eval/human_eval/build_stimuli.py --participants 20

human-eval-oauth:
	.venv/bin/python eval/human_eval/setup_oauth.py --open-console

human-eval-forms:
	.venv/bin/python eval/human_eval/generate_forms.py --participants P001

human-eval-forms-all:
	.venv/bin/python eval/human_eval/generate_forms.py --participants P002 P003 P004 P005 P006 P007 P008 P009 P010 --append-links

human-eval-forms-extended:
	.venv/bin/python eval/human_eval/generate_forms.py --participants P011 P012 P013 P014 P015 P016 P017 P018 P019 P020 --append-links
	$(MAKE) human-eval-portal

human-eval-forms-refresh:
	.venv/bin/python eval/human_eval/generate_forms.py --participants \
		P001 P002 P003 P004 P005 P006 P007 P008 P009 P010 \
		P011 P012 P013 P014 P015 P016 P017 P018 P019 P020 --append-links

human-eval-portal:
	.venv/bin/python eval/human_eval/build_portal.py

significance-test:
	.venv/bin/python eval/significance_test.py

notebook:
	.venv/bin/jupyter lab notebooks/

paper:
	bash scripts/build_paper.sh
