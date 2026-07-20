# arXiv Submission Guide

**Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data**

## Upload these files

Primary (recommended): upload the source tarball

- `MSHA_Safety_Agent_arXiv_source.tar.gz`

Or upload individually from `arxiv_bundle/`:

- `main.tex`
- `references.bib`

Optional: attach `MSHA_Safety_Agent.pdf` for visual check.

## Compile locally

```bash
make paper
# or
bash scripts/build_paper.sh
```

Manual sequence:

```bash
cd paper/
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

## Metadata for arXiv

| Field | Value |
|-------|-------|
| Title | Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis: A Study Using U.S. Mine Safety and Health Administration Data |
| Author | Wisdom Dogah |
| Affiliation | University of Mines and Technology (UMaT), Tarkwa, Ghana; BlackMatrix AI Research, Accra, Ghana |
| Email | wisdom@blackmatrix.io |
| Primary category | **cs.AI** (Artificial Intelligence) |
| Secondary / cross-list | **cs.LG**; optionally **cs.CL** or applied domains |
| Comments | Source code, benchmark, and reproduction guide: https://github.com/dogahwisdom/msha-safety-agent |

## Integrity checklist (pre-submit)

- [x] Benchmark numbers match offline evaluation (93.3% overall, 100% tool selection)
- [x] Classifier holdout metrics match trained model evaluation (0.574 acc, 0.562 macro F1)
- [x] Ollama supplementary numbers reported separately (Section 6.5), not as primary claims
- [x] Incomplete Groq runs are not included as paper results
- [x] Bibliography entries are real papers with DOI/arXiv where available
- [x] No em dashes in manuscript source
- [x] Traxia-style professional article layout (geometry, natbib, hyperref)
- [ ] You have reviewed the PDF page-by-page before clicking Submit

## Archive

The working manuscript is `main.tex` + `MSHA_Safety_Agent.pdf`.
