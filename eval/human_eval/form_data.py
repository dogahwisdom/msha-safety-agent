"""Load human-eval stimulus data for Google Forms generation and export."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parent / "generated"
MATERIALS_PATH = Path(__file__).resolve().parent / "materials.md"
CONSENT_PATH = Path(__file__).resolve().parent / "consent_form.md"

ESS_ITEMS = tuple(f"ESS-{idx}" for idx in range(1, 10))

ESS_STATEMENTS: dict[str, str] = {
    "ESS-1": "From the explanation, I understand how the MSHA safety system works.",
    "ESS-2": "This explanation of how the MSHA safety system works is satisfying.",
    "ESS-3": "This explanation of how the MSHA safety system works has sufficient detail.",
    "ESS-4": "This explanation seems complete.",
    "ESS-5": "This explanation shows me how accurate the MSHA safety system is.",
    "ESS-6": "This explanation shows me how reliable the MSHA safety system is.",
    "ESS-7": "This explanation tells me how to use the MSHA safety system.",
    "ESS-8": "This explanation is useful to my goals.",
    "ESS-9": "This explanation helps me know when I should trust and not trust the MSHA safety system.",
}

SCALE_COLUMNS: list[str] = [
    "1 - I disagree strongly",
    "2 - I disagree somewhat",
    "3 - I'm neutral about it",
    "4 - I agree somewhat",
    "5 - I agree strongly",
]

CONSENT_CHECKBOX_TEXT = (
    "I confirm that I meet the eligibility criteria, I have had the opportunity to "
    "ask questions, and I agree to participate."
)


@dataclass(frozen=True)
class StimulusBlock:
    stimulus_id: str
    question_id: str
    category: str
    system_blinded_label: str
    question: str
    answer_text: str


@dataclass(frozen=True)
class QuestionSection:
    question_id: str
    category: str
    question: str
    answers: tuple[StimulusBlock, ...]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_stimuli_blinded(path: Path | None = None) -> dict[str, dict[str, str]]:
    csv_path = path or (GENERATED_DIR / "stimuli_blinded.csv")
    rows = _read_csv(csv_path)
    return {row["stimulus_id"]: row for row in rows}


def load_participant_blocks(
    participant_id: str,
    *,
    generated_dir: Path | None = None,
) -> list[StimulusBlock]:
    base = generated_dir or GENERATED_DIR
    template_path = base / "response_templates" / f"{participant_id}_responses.csv"
    if not template_path.exists():
        raise FileNotFoundError(f"Missing response template: {template_path}")
    blinded = load_stimuli_blinded(base / "stimuli_blinded.csv")
    blocks: list[StimulusBlock] = []
    for row in _read_csv(template_path):
        meta = blinded[row["stimulus_id"]]
        blocks.append(
            StimulusBlock(
                stimulus_id=row["stimulus_id"],
                question_id=row["question_id"],
                category=row["category"],
                system_blinded_label=meta["system_blinded_label"],
                question=meta["question"],
                answer_text=meta["answer_text"],
            )
        )
    return blocks


def group_blocks_by_question(blocks: list[StimulusBlock]) -> list[QuestionSection]:
    sections: list[QuestionSection] = []
    for question_id, group in groupby(blocks, key=lambda block: block.question_id):
        answers = tuple(group)
        if len(answers) != 3:
            raise ValueError(f"Expected 3 answers for {question_id}, found {len(answers)}")
        sections.append(
            QuestionSection(
                question_id=question_id,
                category=answers[0].category,
                question=answers[0].question,
                answers=answers,
            )
        )
    return sections


def form_title(participant_id: str) -> str:
    return "MSHA Safety System Explanation Evaluation"


def form_description(participant_id: str) -> str:
    return (
        f"University of Mines and Technology (UMaT). "
        f"Estimated time: 45 to 60 minutes. Participant ID: {participant_id}. "
        "Participation is voluntary and confidential."
    )


TRANSPARENCY_LINE = (
    "These systems include large language model-based and other automated baselines."
)


def welcome_page_text() -> str:
    return (
        "Thank you for taking part in this study.\n\n"
        "Purpose\n"
        "We are evaluating system-generated explanations for Mine Safety and Health "
        "Administration (MSHA) safety questions. Your ratings will help us understand "
        "which explanations are clear, complete, and trustworthy. "
        f"{TRANSPARENCY_LINE}\n\n"
        "What you will do\n"
        "1. Read 12 mine safety questions.\n"
        "2. Review three blinded explanations for each question (System A, System B, System C).\n"
        "3. Rate nine Explanation Satisfaction Scale statements about each explanation "
        "using a 1 to 5 scale.\n"
        "4. Optionally leave a short comment if something was missing from an explanation.\n\n"
        "Important\n"
        "1. You are rating explanation quality, not whether the factual answer is correct.\n"
        "2. The three systems are blinded. Do not try to guess which system produced each explanation.\n"
        "3. There are 36 rating blocks in total (12 questions, 3 systems each).\n"
        "4. You may pause and return later if needed.\n\n"
        "Eligibility\n"
        "Mining engineering faculty or senior undergraduate students at UMaT.\n\n"
        "Continue to the next page for the informed consent statement."
    )


def consent_page_text() -> str:
    return (
        "You are invited to participate in a research study on system-generated "
        "explanations for mine safety questions. The study is conducted at the "
        "University of Mines and Technology and may be reported in academic publications.\n\n"
        "Your rights\n"
        "Participation is voluntary. You may skip any question or withdraw at any time "
        "without penalty.\n\n"
        "Confidentiality\n"
        "Responses are stored under a pseudonymous participant ID. This form does not "
        "collect your name. The researcher uses the ID only for session management. "
        "Published results report combined scores, not individual identities.\n\n"
        "Risks and benefits\n"
        "There are no physical risks. Some accident descriptions may be distressing; "
        "you may skip any item or stop at any time. There is no payment. Your feedback "
        "may help improve decision-support explanation tools for mining engineering.\n\n"
        "Questions\n"
        "If you have questions about the study, contact the study team before continuing.\n\n"
        "Check the box below to confirm your agreement to participate."
    )


def rating_instructions_text() -> str:
    scale_lines = "\n".join(f"{idx + 1}. {label}" for idx, label in enumerate(SCALE_COLUMNS))
    ess_preview = "\n".join(
        f"{idx + 1}. {ESS_STATEMENTS[item]}" for idx, item in enumerate(ESS_ITEMS[:3])
    )
    return (
        "For each answer (System A, B, or C), please follow these steps:\n"
        "1. Read the question and the system explanation carefully.\n"
        "2. Complete all nine Explanation Satisfaction Scale (ESS) statements for that answer.\n"
        "3. Add an optional comment if the scale does not capture something important.\n\n"
        "Rating scale:\n"
        f"{scale_lines}\n\n"
        "Sample ESS statements (all nine appear after each answer):\n"
        f"{ess_preview}\n"
        "4. Six additional statements cover completeness, accuracy, reliability, "
        "usability, usefulness, and trust.\n\n"
        "Guidance:\n"
        "1. Rate the explanation shown, not outside knowledge.\n"
        "2. If an answer is vague, rate how clearly the system explained its reasoning.\n"
        "3. Use the comment box for anything not covered by the nine statements.\n\n"
        "When you are ready, continue to Question 1."
    )


def study_intro_text(participant_id: str) -> str:
    """Short form header shown under the title in Google Forms."""
    return form_description(participant_id)
