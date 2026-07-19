"""Generate blinded human-eval stimulus sheets from benchmark runs."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

RESULTS_PATH = Path(__file__).resolve().parents[1] / "results" / "benchmark_runs.json"
OUT_DIR = Path(__file__).resolve().parent


def build_stimuli(seed: int = 42, max_questions: int = 12) -> Path:
    if not RESULTS_PATH.exists():
        raise FileNotFoundError("Run eval/run_benchmark.py first to create benchmark_runs.json")
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    rows = payload["results"]
    question_ids = sorted({r["question_id"] for r in rows})[:max_questions]
    labels = ["A", "B", "C"]
    mapping = []
    stimuli = []
    stimulus_id = 1
    for qid in question_ids:
        q_rows = [r for r in rows if r["question_id"] == qid]
        random.Random(seed + stimulus_id).shuffle(q_rows)
        for idx, row in enumerate(q_rows):
            blind = labels[idx % 3]
            sid = f"S{stimulus_id:03d}"
            stimuli.append(
                {
                    "stimulus_id": sid,
                    "question_id": qid,
                    "system_blinded_label": blind,
                    "system_actual": row["system"],
                    "question": row["question"],
                    "answer_text": row["answer"],
                }
            )
            mapping.append(
                {
                    "stimulus_id": sid,
                    "question_id": qid,
                    "system_blinded_label": blind,
                    "system_actual": row["system"],
                }
            )
            stimulus_id += 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stim_path = OUT_DIR / "stimuli.csv"
    map_path = OUT_DIR / "randomization_key.csv"
    with stim_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(stimuli[0].keys()))
        writer.writeheader()
        writer.writerows(stimuli)
    with map_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapping[0].keys()))
        writer.writeheader()
        writer.writerows(mapping)
    return stim_path


if __name__ == "__main__":
    path = build_stimuli()
    print(f"Wrote {path}")
