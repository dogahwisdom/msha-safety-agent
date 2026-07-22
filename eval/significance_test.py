"""McNemar's test on paired per-question benchmark correctness (Groq primary run)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.score import REFERENCES_PATH, _score_row  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results" / "significance_groq_fixed.json"


def _load_correctness(benchmark_path: Path) -> dict[str, dict[str, bool]]:
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    references = json.loads(REFERENCES_PATH.read_text(encoding="utf-8"))
    by_question: dict[str, dict[str, bool]] = {}
    for row in payload["results"]:
        qid = row["question_id"]
        system = row["system"]
        ref = references[qid]
        score = _score_row(row, ref)
        by_question.setdefault(qid, {})[system] = bool(score["correct"])
    return by_question


def _mcnemar(system_a: dict[str, bool], system_b: dict[str, bool]) -> dict[str, Any]:
    """Compare system_a vs system_b on the same question ids."""
    question_ids = sorted(set(system_a) & set(system_b))
    if len(question_ids) != 60:
        raise ValueError(f"Expected 60 paired questions, found {len(question_ids)}")

    both_correct = both_wrong = 0
    a_wrong_b_right = 0
    a_right_b_wrong = 0
    for qid in question_ids:
        a_ok = system_a[qid]
        b_ok = system_b[qid]
        if a_ok and b_ok:
            both_correct += 1
        elif not a_ok and not b_ok:
            both_wrong += 1
        elif not a_ok and b_ok:
            a_wrong_b_right += 1
        elif a_ok and not b_ok:
            a_right_b_wrong += 1

    discordant = a_wrong_b_right + a_right_b_wrong
    if discordant == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        try:
            from scipy.stats import chi2
        except ImportError as exc:
            raise ImportError("scipy is required for McNemar p-values") from exc
        statistic = (abs(a_wrong_b_right - a_right_b_wrong) - 1) ** 2 / discordant
        p_value = float(chi2.sf(statistic, df=1))

    n = len(question_ids)
    a_correct = sum(system_a[q] for q in question_ids)
    b_correct = sum(system_b[q] for q in question_ids)
    return {
        "n_questions": n,
        "system_a_correct": a_correct,
        "system_a_accuracy": round(a_correct / n, 4),
        "system_b_correct": b_correct,
        "system_b_accuracy": round(b_correct / n, 4),
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "a_wrong_b_right": a_wrong_b_right,
        "a_right_b_wrong": a_right_b_wrong,
        "mcnemar_statistic": round(statistic, 4),
        "p_value": round(p_value, 4),
        "significant_at_0_05": p_value < 0.05,
    }


def run_significance_tests(benchmark_path: Path) -> dict[str, Any]:
    by_question = _load_correctness(benchmark_path)
    agent = {qid: systems["agent"] for qid, systems in by_question.items() if "agent" in systems}
    classifier = {
        qid: systems["classifier_baseline"]
        for qid, systems in by_question.items()
        if "classifier_baseline" in systems
    }
    rag = {qid: systems["rag_baseline"] for qid, systems in by_question.items() if "rag_baseline" in systems}

    comparisons = {
        "agent_vs_classifier_baseline": _mcnemar(agent, classifier),
        "agent_vs_rag_baseline": _mcnemar(agent, rag),
    }
    return {
        "benchmark_path": str(benchmark_path),
        "test": "mcnemar",
        "alpha": 0.05,
        "comparisons": comparisons,
    }


def _default_benchmark_path() -> Path:
    name = os.environ.get("BENCHMARK_OUTPUT", "benchmark_runs_groq_fixed.json")
    return Path(__file__).resolve().parent / "results" / name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help="Benchmark JSON (default: eval/results/benchmark_runs_groq_fixed.json).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write JSON results.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    benchmark_path = args.benchmark or _default_benchmark_path()
    results = run_significance_tests(benchmark_path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
