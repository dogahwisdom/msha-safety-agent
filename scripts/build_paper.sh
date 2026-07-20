#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER="$ROOT/paper"
BUNDLE="$PAPER/arxiv_bundle"
TARBALL="$PAPER/MSHA_Safety_Agent_arXiv_source.tar.gz"
PDF_NAME="MSHA_Safety_Agent.pdf"

cd "$PAPER"

echo "==> Compiling LaTeX manuscript"
pdflatex -interaction=nonstopmode main.tex >/dev/null
bibtex main
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex

if [[ ! -f main.pdf ]]; then
  echo "ERROR: main.pdf was not produced" >&2
  exit 1
fi

cp -f main.pdf "$PDF_NAME"
echo "==> Wrote $PAPER/$PDF_NAME"

mkdir -p "$BUNDLE"
cp -f main.tex references.bib "$BUNDLE/"
cat > "$BUNDLE/00README.XXX" <<'EOF'
% arXiv source bundle for:
% Tool-Augmented Language Model Agents for Explainable Mine Safety Risk Analysis
% Compile with: pdflatex main && bibtex main && pdflatex main && pdflatex main
EOF

tar -czf "$TARBALL" -C "$BUNDLE" .
echo "==> Wrote $TARBALL"

echo "Done."
