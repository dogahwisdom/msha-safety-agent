"""Generate blinded human-eval stimulus sheets from benchmark runs."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.human_eval.form_data import ESS_ITEMS, format_answer_for_display

DEFAULT_RESULTS = (
    Path(__file__).resolve().parents[1] / "results" / "benchmark_runs_groq_fixed.json"
)
OUT_DIR = Path(__file__).resolve().parent / "generated"
SYSTEM_LABELS = ("A", "B", "C")


def load_benchmark_rows(results_path: Path) -> list[dict]:
    if not results_path.exists():
        raise FileNotFoundError(
            f"Benchmark results not found: {results_path}. "
            "Run the Groq benchmark first (make eval-groq)."
        )
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    rows = payload["results"]
    if not rows:
        raise ValueError(f"No benchmark rows in {results_path}")
    return rows


def question_category(question_id: str) -> str:
    return question_id.split("-", 1)[0]


def select_question_ids(
    rows: list[dict],
    *,
    questions_per_category: int,
    seed: int,
) -> list[str]:
    by_category: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        qid = row["question_id"]
        if qid not in by_category[question_category(qid)]:
            by_category[question_category(qid)].append(qid)
    for category in by_category:
        by_category[category].sort()

    selected: list[str] = []
    for category in sorted(by_category):
        pool = by_category[category]
        if len(pool) < questions_per_category:
            raise ValueError(
                f"Category {category} has only {len(pool)} questions; "
                f"requested {questions_per_category}."
            )
        rng = random.Random(seed + hash(category) % 10_000)
        selected.extend(rng.sample(pool, questions_per_category))
    return sorted(selected)


def build_stimulus_rows(
    rows: list[dict],
    question_ids: list[str],
    *,
    seed: int,
) -> tuple[list[dict], list[dict]]:
    """Return participant-safe stimuli and researcher randomization key rows."""
    stimuli: list[dict] = []
    mapping: list[dict] = []
    stimulus_id = 1
    for qid in question_ids:
        q_rows = [row for row in rows if row["question_id"] == qid]
        if len(q_rows) != 3:
            raise ValueError(f"Expected 3 system answers for {qid}, found {len(q_rows)}")
        rng = random.Random(seed + stimulus_id)
        shuffled = q_rows[:]
        rng.shuffle(shuffled)
        question_text = shuffled[0]["question"]
        category = shuffled[0].get("category") or question_category(qid)
        for idx, row in enumerate(shuffled):
            blind = SYSTEM_LABELS[idx]
            sid = f"S{stimulus_id:03d}"
            stimuli.append(
                {
                    "stimulus_id": sid,
                    "question_id": qid,
                    "category": category,
                    "system_blinded_label": blind,
                    "question": question_text,
                    "answer_text": format_answer_for_display(row["answer"]),
                }
            )
            mapping.append(
                {
                    "stimulus_id": sid,
                    "question_id": qid,
                    "category": category,
                    "system_blinded_label": blind,
                    "system_actual": row["system"],
                }
            )
            stimulus_id += 1
    return stimuli, mapping


def participant_question_order(stimuli: list[dict], *, seed: int) -> list[str]:
    question_ids = sorted({row["question_id"] for row in stimuli})
    order = question_ids[:]
    random.Random(seed).shuffle(order)
    return order


def stimuli_for_participant(
    stimuli: list[dict],
    question_order: list[str],
) -> list[dict]:
    by_question: dict[str, list[dict]] = defaultdict(list)
    for row in stimuli:
        by_question[row["question_id"]].append(row)
    ordered: list[dict] = []
    display_idx = 1
    for qid in question_order:
        block = sorted(by_question[qid], key=lambda row: row["system_blinded_label"])
        for row in block:
            ordered.append({**row, "display_order": display_idx})
            display_idx += 1
    return ordered


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_participant_packet(
    path: Path,
    *,
    participant_id: str,
    stimuli: list[dict],
    results_source: Path,
) -> None:
    lines = [
        "# MSHA Safety System Explanation Study",
        "",
        f"Participant ID: `{participant_id}`",
        "",
        "You will read mine safety questions and one system answer at a time.",
        "Rate each answer using the nine statements on the 1 to 5 scale below.",
        "Do not discuss answers with other participants during the session.",
        "",
        "**Scale:** 5 = agree strongly, 4 = agree somewhat, 3 = neutral, "
        "2 = disagree somewhat, 1 = disagree strongly.",
        "",
        "## Explanation Satisfaction Scale",
        "",
    ]
    for idx in range(1, 10):
        lines.append(
            f"- ESS-{idx}: See `materials.md` item ESS-{idx} "
            '(replace "MSHA safety system" as written there).'
        )
    lines.extend(
        [
            "",
            f"Benchmark source: `{results_source.name}` (Groq primary run).",
            "",
        ]
    )
    for row in stimuli:
        lines.extend(
            [
                f"## {row['stimulus_id']} (item {row['display_order']} of {len(stimuli)})",
                "",
                f"**Category:** {row['category']}",
                "",
                "**Question**",
                "",
                row["question"],
                "",
                f"**Answer (System {row['system_blinded_label']})**",
                "",
                row["answer_text"],
                "",
                "**Ratings (1 to 5)**",
                "",
            ]
        )
        for item in ESS_ITEMS:
            lines.append(f"- {item}: ____")
        lines.extend(["", "**Optional comment:** What was missing or unclear in this system's explanation?", "", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_response_template(path: Path, *, participant_id: str, stimuli: list[dict]) -> None:
    fieldnames = ["participant_id", "stimulus_id", "question_id", "category", *ESS_ITEMS, "comment"]
    rows = [
        {
            "participant_id": participant_id,
            "stimulus_id": row["stimulus_id"],
            "question_id": row["question_id"],
            "category": row["category"],
            **{item: "" for item in ESS_ITEMS},
            "comment": "",
        }
        for row in stimuli
    ]
    write_csv(path, rows, fieldnames)


def build_stimuli(
    *,
    results_path: Path = DEFAULT_RESULTS,
    out_dir: Path = OUT_DIR,
    seed: int = 42,
    questions_per_category: int = 4,
    participant_count: int = 1,
    participant_prefix: str = "P",
) -> Path:
    rows = load_benchmark_rows(results_path)
    question_ids = select_question_ids(
        rows,
        questions_per_category=questions_per_category,
        seed=seed,
    )
    stimuli, mapping = build_stimulus_rows(rows, question_ids, seed=seed)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "results_path": str(results_path),
        "seed": seed,
        "questions_per_category": questions_per_category,
        "question_ids": question_ids,
        "stimulus_count": len(stimuli),
        "participant_count": participant_count,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    write_csv(
        out_dir / "stimuli_blinded.csv",
        stimuli,
        [
            "stimulus_id",
            "question_id",
            "category",
            "system_blinded_label",
            "question",
            "answer_text",
        ],
    )
    write_csv(
        out_dir / "randomization_key.csv",
        mapping,
        [
            "stimulus_id",
            "question_id",
            "category",
            "system_blinded_label",
            "system_actual",
        ],
    )

    packets_dir = out_dir / "packets"
    responses_dir = out_dir / "response_templates"
    for idx in range(participant_count):
        participant_id = f"{participant_prefix}{idx + 1:03d}"
        order = participant_question_order(stimuli, seed=seed + idx + 1)
        ordered = stimuli_for_participant(stimuli, order)
        write_participant_packet(
            packets_dir / f"{participant_id}_packet.md",
            participant_id=participant_id,
            stimuli=ordered,
            results_source=results_path,
        )
        write_response_template(
            responses_dir / f"{participant_id}_responses.csv",
            participant_id=participant_id,
            stimuli=ordered,
        )

    return out_dir / "stimuli_blinded.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS,
        help="Benchmark JSON from eval/run_benchmark.py (default: Groq primary run).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="Output directory for generated survey materials.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--questions-per-category",
        type=int,
        default=4,
        help="Number of benchmark questions per category (CLS/TRD/CASE).",
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=20,
        help="Number of participant packets to generate (different question order).",
    )
    parser.add_argument("--participant-prefix", default="P")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_stimuli(
        results_path=args.results,
        out_dir=args.out_dir,
        seed=args.seed,
        questions_per_category=args.questions_per_category,
        participant_count=args.participants,
        participant_prefix=args.participant_prefix,
    )
    print(f"Wrote blinded stimuli to {path.parent}")
    print(f"Participant packets: {path.parent / 'packets'}")
    print(f"Response templates: {path.parent / 'response_templates'}")
    print(f"Randomization key (researcher only): {path.parent / 'randomization_key.csv'}")


if __name__ == "__main__":
    main()
