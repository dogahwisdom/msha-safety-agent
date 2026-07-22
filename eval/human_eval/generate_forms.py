"""Create Google Forms from blinded human-eval participant packets."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.human_eval.form_data import (
    CONSENT_CHECKBOX_TEXT,
    ESS_ITEMS,
    ESS_STATEMENTS,
    SCALE_COLUMNS,
    QuestionSection,
    StimulusBlock,
    consent_page_text,
    form_description,
    form_title,
    group_blocks_by_question,
    load_participant_blocks,
    rating_instructions_text,
    welcome_page_text,
)
from eval.human_eval.google_auth import build_forms_service, get_credentials

try:
    from eval.human_eval.build_portal import write_portal
except ImportError:
    write_portal = None  # type: ignore[assignment,misc]

GENERATED_DIR = Path(__file__).resolve().parent / "generated"
FORM_LINKS_PATH = GENERATED_DIR / "form_links.csv"
FORM_REGISTRY_PATH = GENERATED_DIR / "form_registry.json"
BATCH_CHUNK_SIZE = 40
STIMULUS_ID_PATTERN = re.compile(r"\b(S\d{3})\b")


def _stimulus_id_from_item(item: dict[str, Any]) -> str | None:
    title = item.get("title", "")
    description = item.get("description", "")
    for text in (title, description):
        match = STIMULUS_ID_PATTERN.search(text)
        if match:
            return match.group(1)
    if title.startswith("["):
        return title.split("]", 1)[0].lstrip("[")
    return None


def _grid_question_item(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "questionGroupItem": {
            "grid": {
                "columns": {
                    "type": "RADIO",
                    "options": [{"value": label} for label in SCALE_COLUMNS],
                },
            },
            "questions": [
                {"rowQuestion": {"title": ESS_STATEMENTS[item]}} for item in ESS_ITEMS
            ],
        },
    }


def _text_block_item(title: str, body: str) -> dict[str, Any]:
    return {
        "title": title,
        "description": body[:15000],
        "textItem": {},
    }


def _page_break_item(title: str, *, description: str = "") -> dict[str, Any]:
    item: dict[str, Any] = {"title": title, "pageBreakItem": {}}
    if description:
        item["description"] = description[:15000]
    return item


def _comment_question_item(stimulus_id: str) -> dict[str, Any]:
    return {
        "title": "Optional comment",
        "description": (
            f"Response ID: {stimulus_id}. "
            "What was missing from this explanation? (Optional)"
        ),
        "questionItem": {
            "question": {
                "required": False,
                "textQuestion": {"paragraph": True},
            }
        },
    }


def _answer_block_requests(answer: StimulusBlock) -> list[dict[str, Any]]:
    return [
        {
            "createItem": {
                "item": _text_block_item(
                    f"System {answer.system_blinded_label}",
                    answer.answer_text,
                ),
            }
        },
        {
            "createItem": {
                "item": _grid_question_item(
                    f"Explanation Satisfaction Scale (Response {answer.stimulus_id})"
                ),
            }
        },
        {
            "createItem": {
                "item": _comment_question_item(answer.stimulus_id),
            }
        },
    ]


def _intro_section_requests() -> list[dict[str, Any]]:
    return [
        {
            "createItem": {
                "item": _page_break_item(
                    "Study overview",
                    description=welcome_page_text(),
                ),
            }
        },
        {
            "createItem": {
                "item": _page_break_item(
                    "Informed consent",
                    description=consent_page_text(),
                ),
            }
        },
        {
            "createItem": {
                "item": {
                    "title": "Consent confirmation",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "CHECKBOX",
                                "options": [{"value": CONSENT_CHECKBOX_TEXT}],
                            },
                        }
                    },
                },
            }
        },
        {
            "createItem": {
                "item": _page_break_item(
                    "Rating instructions",
                    description=rating_instructions_text(),
                ),
            }
        },
    ]


def build_create_requests(
    participant_id: str,
    sections: list[QuestionSection],
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    total_questions = len(sections)
    requests.append(
        {
            "updateFormInfo": {
                "info": {
                    "title": form_title(participant_id),
                    "description": form_description(participant_id),
                },
                "updateMask": "title,description",
            }
        }
    )
    requests.append(
        {
            "updateSettings": {
                "settings": {
                    "emailCollectionType": "DO_NOT_COLLECT",
                },
                "updateMask": "emailCollectionType",
            }
        }
    )
    requests.extend(_intro_section_requests())

    for section_number, section in enumerate(sections, start=1):
        requests.append(
            {
                "createItem": {
                    "item": _page_break_item(
                        f"Question {section_number} of {total_questions}",
                        description=(
                            f"Category: {section.category}\n\n{section.question}"
                        ),
                    ),
                }
            }
        )
        for answer in section.answers:
            requests.extend(_answer_block_requests(answer))
    return requests


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _assign_create_locations(requests: list[dict[str, Any]]) -> None:
    index = 0
    for request in requests:
        if "createItem" in request:
            request["createItem"]["location"] = {"index": index}
            index += 1


def _apply_batch_updates(service, form_id: str, requests: list[dict[str, Any]]) -> None:
    _assign_create_locations(requests)
    for chunk in _chunked(requests, BATCH_CHUNK_SIZE):
        service.forms().batchUpdate(formId=form_id, body={"requests": chunk}).execute()


def _form_url(form_id: str, form_body: dict[str, Any]) -> str:
    if "responderUri" in form_body:
        return form_body["responderUri"]
    return f"https://docs.google.com/forms/d/{form_id}/viewform"


def _extract_registry(form_body: dict[str, Any], participant_id: str) -> dict[str, Any]:
    registry_items: list[dict[str, Any]] = []
    for item in form_body.get("items", []):
        stimulus_id = _stimulus_id_from_item(item)
        if not stimulus_id:
            continue
        question_item = item.get("questionItem", {}).get("question", {})
        question_group = item.get("questionGroupItem", {})
        if "grid" in question_group:
            row_question_ids = [
                question.get("questionId", "")
                for question in question_group.get("questions", [])
                if question.get("questionId")
            ]
            registry_items.append(
                {
                    "stimulus_id": stimulus_id,
                    "grid_item_id": item.get("itemId", ""),
                    "grid_row_question_ids": row_question_ids,
                }
            )
        elif "grid" in question_item:
            registry_items.append(
                {
                    "stimulus_id": stimulus_id,
                    "grid_item_id": item.get("itemId", ""),
                    "grid_question_id": question_item.get("questionId", ""),
                }
            )
        elif "textQuestion" in question_item:
            registry_items.append(
                {
                    "stimulus_id": stimulus_id,
                    "comment_item_id": item.get("itemId", ""),
                    "comment_question_id": question_item.get("questionId", ""),
                }
            )
    merged: dict[str, dict[str, Any]] = {}
    for entry in registry_items:
        sid = entry["stimulus_id"]
        merged.setdefault(sid, {"stimulus_id": sid})
        merged[sid].update({k: v for k, v in entry.items() if k != "stimulus_id"})
    return {
        "participant_id": participant_id,
        "form_id": form_body.get("formId", ""),
        "form_url": _form_url(form_body.get("formId", ""), form_body),
        "stimuli": [merged[sid] for sid in sorted(merged)],
    }


def create_form_for_participant(
    service,
    participant_id: str,
    *,
    generated_dir: Path = GENERATED_DIR,
) -> dict[str, Any]:
    blocks = load_participant_blocks(participant_id, generated_dir=generated_dir)
    sections = group_blocks_by_question(blocks)
    if len(sections) != 12:
        raise ValueError(f"{participant_id}: expected 12 question sections, found {len(sections)}")
    if len(blocks) != 36:
        raise ValueError(f"{participant_id}: expected 36 stimulus blocks, found {len(blocks)}")

    create_body = {
        "info": {
            "title": form_title(participant_id),
            "documentTitle": f"MSHA Eval {participant_id}",
        }
    }
    form = service.forms().create(body=create_body).execute()
    form_id = form["formId"]
    requests = build_create_requests(participant_id, sections)
    _apply_batch_updates(service, form_id, requests)
    form_body = service.forms().get(formId=form_id).execute()
    registry = _extract_registry(form_body, participant_id)
    registry["form_url"] = _form_url(form_id, form_body)
    return registry


def write_form_links(rows: list[dict[str, str]], path: Path = FORM_LINKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["participant_id", "form_url"])
        writer.writeheader()
        writer.writerows(rows)


def write_form_registry(entries: dict[str, Any], path: Path = FORM_REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--participants",
        nargs="+",
        default=["P001"],
        help="Participant IDs to generate forms for (default: P001 only).",
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=GENERATED_DIR,
        help="Directory containing packets and response templates.",
    )
    parser.add_argument(
        "--append-links",
        action="store_true",
        help="Append to form_links.csv instead of overwriting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    creds = get_credentials()
    service = build_forms_service(creds)

    link_rows: list[dict[str, str]] = []
    registry: dict[str, Any] = {}
    if args.append_links and FORM_REGISTRY_PATH.exists():
        registry = json.loads(FORM_REGISTRY_PATH.read_text(encoding="utf-8"))

    for participant_id in args.participants:
        result = create_form_for_participant(
            service,
            participant_id,
            generated_dir=args.generated_dir,
        )
        registry[participant_id] = result
        link_rows.append(
            {"participant_id": participant_id, "form_url": result["form_url"]}
        )
        print(f"{participant_id}: {result['form_url']}")

    if args.append_links and FORM_LINKS_PATH.exists():
        existing = _read_existing_links(FORM_LINKS_PATH)
        by_id = {row["participant_id"]: row for row in existing}
        by_id.update({row["participant_id"]: row for row in link_rows})
        link_rows = [by_id[pid] for pid in sorted(by_id)]
    write_form_links(link_rows)
    write_form_registry(registry)
    print(f"Wrote {FORM_LINKS_PATH}")
    print(f"Wrote {FORM_REGISTRY_PATH}")
    if write_portal is not None:
        portal_path = write_portal(links_path=FORM_LINKS_PATH)
        print(f"Wrote {portal_path}")


def _read_existing_links(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


if __name__ == "__main__":
    main()
