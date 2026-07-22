#!/usr/bin/env bash
# Run Groq benchmark one system at a time; checkpoint after every question.
# Resume: bash scripts/run_groq_benchmark.sh
# Fresh:  BENCHMARK_FRESH=1 bash scripts/run_groq_benchmark.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${GROQ_API_KEY:-}" ]]; then
  echo "Set GROQ_API_KEY before running this script." >&2
  exit 1
fi

export LLM_PROVIDER=groq
export GROQ_MODEL="${GROQ_MODEL:-llama-3.3-70b-versatile}"
export GROQ_BENCHMARK_DELAY_S="${GROQ_BENCHMARK_DELAY_S:-2.5}"
export BENCHMARK_OUTPUT="${BENCHMARK_OUTPUT:-benchmark_runs_groq_fixed.json}"
RESULTS="$ROOT/eval/results"
PARTIAL="$RESULTS/benchmark_runs_groq_partial.jsonl"
OUT="$RESULTS/$BENCHMARK_OUTPUT"
export BENCHMARK_CHECKPOINT="$PARTIAL"

if [[ "${BENCHMARK_FRESH:-}" == "1" ]]; then
  rm -f "$PARTIAL"
fi
mkdir -p "$RESULTS"
touch "$PARTIAL"

run_system() {
  local system="$1"
  local done
  done="$(.venv/bin/python -c "
import json
from pathlib import Path
p = Path('$PARTIAL')
rows = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
print(sum(1 for row in rows if row.get('system') == '$system'))
")"
  if [[ "$done" -ge 60 ]]; then
    echo "==> Skipping $system ($done/60 already checkpointed)"
    return 0
  fi
  echo "==> Running system: $system ($done/60 checkpointed)"
  BENCHMARK_SYSTEMS="$system" .venv/bin/python eval/run_benchmark.py
}

for system in classifier_baseline agent rag_baseline; do
  run_system "$system"
done

.venv/bin/python - <<PY
import json
from pathlib import Path
rows = [json.loads(line) for line in Path("$PARTIAL").read_text(encoding="utf-8").splitlines() if line.strip()]
out = {
    "questions": 60,
    "mode": "groq",
    "results": rows,
}
Path("$OUT").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(rows)} rows to $OUT")
PY

BENCHMARK_OUTPUT="$BENCHMARK_OUTPUT" .venv/bin/python eval/score.py
echo "DONE $(date -u +%FT%TZ)"
