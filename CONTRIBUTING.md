# Contributing

Thank you for your interest in this research project.

## Getting started

1. Fork the repository and clone your fork.
2. Run `bash scripts/setup.sh` and activate `.venv`.
3. Run `make test` to verify the environment.

## Pull requests

- Keep changes focused — one logical change per PR.
- Run `make test` before opening a PR.
- Update `docs/PROGRESS.md` if you complete a pipeline step or change verified metrics.
- Do not commit secrets (`.env`), raw MSHA dumps, or local artifacts (`data/processed/`, `eval/results/`).

## Reporting issues

Open a GitHub issue with:

- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## Research use

Benchmark questions and reference answers are fixed in `benchmark/` before evaluation. If you propose new questions, add them in a separate branch and document the rationale.
