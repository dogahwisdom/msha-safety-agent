# Human Evaluation Materials (Step 10)

These materials are ready for in-person or survey collection. Do not simulate participant responses in code or reports.

## Study purpose

Participants rate blinded answers from three systems (tool-augmented agent, classifier baseline, RAG baseline) using the Explanation Satisfaction Scale (Hoffman et al., 2023).

## Participant inclusion

- Mining engineering faculty or senior undergraduate students
- Target sample: 10 to 20 participants (exploratory study)

## Procedure

1. Randomize and blind answer order per participant using `eval/human_eval/build_stimuli.py` after benchmark answers exist.
2. Present one question and one system answer at a time.
3. After each answer, administer the nine Explanation Satisfaction Scale items on a 1 to 5 Likert scale:
   - 5 = I agree strongly
   - 4 = I agree somewhat
   - 3 = I'm neutral about it
   - 2 = I disagree somewhat
   - 1 = I disagree strongly
4. Collect optional open comment: "What was missing from this explanation?"

## Explanation Satisfaction Scale (Hoffman et al., 2023)

Replace `[software, algorithm, tool]` with "MSHA safety system" for this study.

| Item | Statement |
|------|-----------|
| ESS-1 | From the explanation, I understand how the MSHA safety system works. |
| ESS-2 | This explanation of how the MSHA safety system works is satisfying. |
| ESS-3 | This explanation of how the MSHA safety system works has sufficient detail. |
| ESS-4 | This explanation seems complete. |
| ESS-5 | This explanation shows me how accurate the MSHA safety system is. |
| ESS-6 | This explanation shows me how reliable the MSHA safety system is. |
| ESS-7 | This explanation tells me how to use the MSHA safety system. |
| ESS-8 | This explanation is useful to my goals. |
| ESS-9 | This explanation helps me know when I should trust and not trust the MSHA safety system. |

## Blinding and randomization

- Label systems as A, B, C only in participant-facing materials.
- Keep the unblinding key in `eval/human_eval/randomization_key.csv` separate from participant packets.
- Do not reveal system identity until after all ratings are collected.

## Response sheet columns

`participant_id, stimulus_id, ESS-1, ESS-2, ESS-3, ESS-4, ESS-5, ESS-6, ESS-7, ESS-8, ESS-9, comment`

## Important

This step ends with materials ready for you to collect real responses in person or by survey. The project must not generate synthetic human evaluation data.
