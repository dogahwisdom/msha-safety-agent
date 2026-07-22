# Facilitator Guide (Step 10)

Use this guide when collecting Explanation Satisfaction Scale ratings in person or by survey.

## Before the session

1. Run the Groq primary benchmark if it is not already on disk:
   ```bash
   make eval-groq
   ```
2. Generate blinded materials:
   ```bash
   make human-eval-stimuli
   ```
3. Print or share one file from `eval/human_eval/generated/packets/` per participant.
4. Keep `eval/human_eval/generated/randomization_key.csv` on the researcher laptop only. Do not give it to participants.

## During the session

1. Assign each participant an ID matching their packet (`P001`, `P002`, ...).
2. Read the consent statement (adapt to your IRB or department policy).
3. Present one stimulus at a time: question text, then one blinded answer labeled A, B, or C.
4. Collect nine Likert ratings (1 to 5) for each stimulus using the ESS items in `materials.md`.
5. Record optional free-text comments.
6. Target 10 to 20 participants for the exploratory study described in the paper draft.

## After the session

1. Copy ratings into the matching file under `eval/human_eval/generated/response_templates/`, or merge all completed sheets into one CSV with columns:
   `participant_id, stimulus_id, question_id, category, ESS-1, ..., ESS-9, comment`
2. Save completed files as `eval/human_eval/responses/P001_completed.csv` (create the folder as needed).
3. Aggregate scores:
   ```bash
   .venv/bin/python eval/human_eval/score_responses.py eval/human_eval/responses/*.csv
   ```
4. Paste the summary into `docs/paper_draft.md` Section 6.5 and rebuild the paper PDF.

## Rules

- Do not simulate or fabricate participant ratings in this repository.
- Do not unblind system names until all ratings are collected.
- If a participant skips a stimulus, leave that row blank and exclude it from scoring.
