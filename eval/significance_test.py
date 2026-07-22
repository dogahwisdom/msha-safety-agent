"""McNemar's exact test on paired per-question benchmark correctness (Groq primary run)."""

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

DEFAULT_SCORES = Path(__file__).resolve().parent / "results" / "scores_groq_fixed.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "results" / "significance_groq_fixed.json"


def load_correctness_by_system(scores_path: Path) -> dict[str, dict[str, bool]]:
    """Load {system: {question_id: correct}} from scored benchmark rows."""
    payload = json.loads(scores_path.read_text(encoding="utf-8"))
    rows = payload["rows"]
    by_system: dict[str, dict[str, bool]] = {}
    for row in rows:
        system = row["system"]
        qid = row["question_id"]
        by_system.setdefault(system, {})[qid] = bool(row["correct"])
    return by_system


def mcnemar_exact(correct_a: dict[str, bool], correct_b: dict[str, bool], label: str) -> dict[str, Any]:
    from scipy.stats import binomtest

    shared_ids = sorted(set(correct_a) & set(correct_b))
    b = c = both_right = both_wrong = 0
    for qid in shared_ids:
        a_ok, b_ok = correct_a[qid], correct_b[qid]
        if a_ok and not b_ok:
            b += 1
        elif not a_ok and b_ok:
            c += 1
        elif a_ok and b_ok:
            both_right += 1
        else:
            both_wrong += 1

    n = len(shared_ids)
    discordant = b + c
    a_correct = sum(correct_a[qid] for qid in shared_ids)
    b_correct = sum(correct_b[qid] for qid in shared_ids)

    print(f"\n{label}")
    print(f"  n={n}, both right={both_right}, both wrong={both_wrong}")
    print(f"  discordant: A-right/B-wrong={b}, A-wrong/B-right={c}, total={discordant}")
    print(f"  A correct={a_correct}/{n} ({100 * a_correct / n:.1f}%), B correct={b_correct}/{n} ({100 * b_correct / n:.1f}%)")

    if discordant == 0:
        print("  No discordant pairs, systems agree on every question.")
        p_value = 1.0
    else:
        p_value = float(binomtest(min(b, c), discordant, 0.5, alternative="two-sided").pvalue)
        print(f"  Exact McNemar p-value: {p_value:.4f}")
        print("  Significant at alpha=0.05" if p_value < 0.05 else "  NOT significant at alpha=0.05")

    return {
        "label": label,
        "n_questions": n,
        "both_correct": both_right,
        "both_wrong": both_wrong,
        "a_right_b_wrong": b,
        "a_wrong_b_right": c,
        "discordant": discordant,
        "system_a_correct": a_correct,
        "system_a_accuracy": round(a_correct / n, 4) if n else 0.0,
        "system_b_correct": b_correct,
        "system_b_accuracy": round(b_correct / n, 4) if n else 0.0,
        "exact_mcnemar_p_value": round(p_value, 4),
        "significant_at_0_05": p_value < 0.05,
    }


def run_significance_tests(scores_path: Path) -> dict[str, Any]:
    by_system = load_correctness_by_system(scores_path)
    agent = by_system["agent"]
    classifier = by_system["classifier_baseline"]
    rag = by_system["rag_baseline"]

    print(f"Scores file: {scores_path}")
    print(f"Systems loaded: {sorted(by_system)}")

    comparisons = {
        "agent_vs_classifier_baseline": mcnemar_exact(
            agent, classifier, "Agent vs classifier baseline"
        ),
        "agent_vs_rag_baseline": mcnemar_exact(agent, rag, "Agent vs RAG baseline"),
    }
    return {
        "scores_path": str(scores_path),
        "test": "mcnemar_exact",
        "alpha": 0.05,
        "comparisons": comparisons,
    }


def _default_scores_path() -> Path:
    name = os.environ.get("SCORES_OUTPUT", "scores_groq_fixed.json")
    return Path(__file__).resolve().parent / "results" / name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scores",
        type=Path,
        default=None,
        help="Scored benchmark JSON with per-row 'correct' field (default: scores_groq_fixed.json).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write JSON summary.",
    )
    parser.add_argument("--quiet-json", action="store_true", help="Skip writing JSON output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scores_path = args.scores or _default_scores_path()
    if not scores_path.exists():
        raise FileNotFoundError(f"Scores file not found: {scores_path}. Run eval/score.py first.")
    results = run_significance_tests(scores_path)
    if not args.quiet_json:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
