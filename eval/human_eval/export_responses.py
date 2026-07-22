"""Export Google Forms responses to score_responses-compatible CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.human_eval.form_data import ESS_ITEMS, GENERATED_DIR, SCALE_COLUMNS, load_participant_blocks
from eval.human_eval.google_auth import build_forms_service, get_credentials

FORM_REGISTRY_PATH = GENERATED_DIR / "form_registry.json"
RESPONSES_DIR = Path(__file__).resolve().parent / "responses"


def _read_registry(path: Path = FORM_REGISTRY_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run eval/human_eval/generate_forms.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _column_index_to_score(column_index: int) -> str:
    if column_index < 0 or column_index >= len(SCALE_COLUMNS):
        raise ValueError(f"Unexpected grid column index: {column_index}")
    return str(column_index + 1)


def _parse_row_choice_answer(answer: dict[str, Any]) -> str:
    texts = answer.get("choiceQuestion", {}).get("answers", [])
    if not texts:
        return ""
    value = texts[0].get("value", "").strip()
    if value in SCALE_COLUMNS:
        return str(SCALE_COLUMNS.index(value) + 1)
    return ""


def _parse_grid_answer(answer: dict[str, Any]) -> dict[str, str]:
    scores: dict[str, str] = {}
    grid = answer.get("gridAnswers", {})
    for row_answer in grid.get("answers", []):
        row_index = int(row_answer["rowIndex"])
        column_index = int(row_answer["columnIndex"])
        if row_index >= len(ESS_ITEMS):
            raise ValueError(f"Unexpected grid row index: {row_index}")
        scores[ESS_ITEMS[row_index]] = _column_index_to_score(column_index)
    return scores


def _parse_comment_answer(answer: dict[str, Any]) -> str:
    texts = answer.get("textAnswers", {}).get("answers", [])
    if not texts:
        return ""
    return texts[0].get("value", "").strip()


def export_participant_responses(
    service,
    participant_id: str,
    registry_entry: dict[str, Any],
    *,
    generated_dir: Path = GENERATED_DIR,
    out_dir: Path = RESPONSES_DIR,
) -> Path:
    form_id = registry_entry["form_id"]
    stimulus_meta = {
        row["stimulus_id"]: row
        for row in load_participant_blocks(participant_id, generated_dir=generated_dir)
    }
    registry_by_stimulus = {row["stimulus_id"]: row for row in registry_entry["stimuli"]}

    response_payload = service.forms().responses().list(formId=form_id).execute()
    responses = response_payload.get("responses", [])
    if not responses:
        raise ValueError(f"No responses yet for {participant_id} (form {form_id}).")
    if len(responses) > 1:
        responses = sorted(
            responses,
            key=lambda row: row.get("lastSubmittedTime", ""),
            reverse=True,
        )[:1]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{participant_id}_completed.csv"
    fieldnames = [
        "participant_id",
        "stimulus_id",
        "question_id",
        "category",
        *ESS_ITEMS,
        "comment",
    ]

    rows: list[dict[str, str]] = []
    for form_response in responses:
        answers = form_response.get("answers", {})
        for stimulus_id, mapping in registry_by_stimulus.items():
            comment_qid = mapping.get("comment_question_id")
            row_question_ids = mapping.get("grid_row_question_ids") or []
            legacy_grid_qid = mapping.get("grid_question_id")
            if not row_question_ids and not legacy_grid_qid:
                continue
            grid_answer = answers.get(legacy_grid_qid) if legacy_grid_qid else None
            if not row_question_ids and not grid_answer:
                continue
            meta = stimulus_meta[stimulus_id]
            row = {
                "participant_id": participant_id,
                "stimulus_id": stimulus_id,
                "question_id": meta.question_id,
                "category": meta.category,
                "comment": "",
            }
            if row_question_ids:
                for ess_item, question_id in zip(ESS_ITEMS, row_question_ids):
                    row_answer = answers.get(question_id)
                    if row_answer:
                        row[ess_item] = _parse_row_choice_answer(row_answer)
            elif grid_answer:
                row.update(_parse_grid_answer(grid_answer))
            if comment_qid and comment_qid in answers:
                row["comment"] = _parse_comment_answer(answers[comment_qid])
            rows.append(row)

    rows.sort(key=lambda row: (row["question_id"], row["stimulus_id"]))
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--participants",
        nargs="*",
        default=None,
        help="Participant IDs to export (default: all entries in form_registry.json).",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=FORM_REGISTRY_PATH,
        help="Form registry JSON from generate_forms.py.",
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=GENERATED_DIR,
        help="Directory containing blinded stimulus CSVs.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=RESPONSES_DIR,
        help="Directory for exported response CSV files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = _read_registry(args.registry)
    participant_ids = args.participants or sorted(registry.keys())
    creds = get_credentials()
    service = build_forms_service(creds)

    for participant_id in participant_ids:
        if participant_id not in registry:
            raise KeyError(f"{participant_id} not found in {args.registry}")
        out_path = export_participant_responses(
            service,
            participant_id,
            registry[participant_id],
            generated_dir=args.generated_dir,
            out_dir=args.out_dir,
        )
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
