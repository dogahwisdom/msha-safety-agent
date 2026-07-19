#!/usr/bin/env bash
# Reproducible environment setup for MSHA Safety Agent research codebase.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
VENV="${VENV:-.venv}"
TORCH_WHEEL_DIR="$ROOT/.wheels"
TORCH_WHEEL="$TORCH_WHEEL_DIR/torch-2.13.0+cpu-cp310-cp310-linux_x86_64.whl"
TORCH_URL="https://download.pytorch.org/whl/cpu/torch-2.13.0%2Bcpu-cp310-cp310-manylinux_2_28_x86_64.whl"

echo "==> Project root: $ROOT"

if [ ! -d "$VENV" ]; then
  echo "==> Creating virtual environment at $VENV"
  "$PYTHON" -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install --upgrade pip setuptools wheel

echo "==> Installing core dependencies (excluding torch)..."
pip install pandas numpy scikit-learn requests joblib pytest openai chromadb \
  jupyter jupyterlab ipykernel matplotlib seaborn \
  sympy networkx jinja2 fsspec filelock huggingface-hub tokenizers tqdm pyyaml

echo "==> Installing PyTorch (CPU)..."
if python -c "import torch" 2>/dev/null; then
  echo "    PyTorch already installed: $(python -c 'import torch; print(torch.__version__)')"
else
  mkdir -p "$TORCH_WHEEL_DIR"
  if [ ! -f "$TORCH_WHEEL" ] || ! python -c "import zipfile; zipfile.ZipFile('$TORCH_WHEEL').testzip()" 2>/dev/null; then
    echo "    Downloading PyTorch wheel (resumable; ~192 MB)..."
    rm -f "$TORCH_WHEEL"
    until curl -fL -C - --retry 20 --retry-delay 3 --connect-timeout 30 --max-time 7200 \
      -A "pip/26.1.2" -o "$TORCH_WHEEL" "$TORCH_URL" \
      && python -c "import zipfile; assert zipfile.ZipFile('$TORCH_WHEEL').testzip() is None"; do
      echo "    Retrying PyTorch download..."
      sleep 3
    done
  fi
  pip install "$TORCH_WHEEL"
fi

echo "==> Installing sentence-transformers..."
pip install "sentence-transformers>=3.0.0"

echo "==> Registering Jupyter kernel: msha-safety-agent"
python -m ipykernel install --user --name=msha-safety-agent --display-name="MSHA Safety Agent"

if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "==> Created .env from .env.example (add OPENAI_API_KEY for agent notebooks)"
fi

echo ""
echo "Setup complete. Activate with: source $VENV/bin/activate"
echo "Run notebooks: jupyter lab notebooks/"
echo "Run tests: pytest tests/ -v"
