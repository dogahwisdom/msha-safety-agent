# Hosting the participant portal (pre-flight checklist)

Use this checklist before sharing the study with real participants.

## 1. Ethics and consent (blocking)

- [ ] UMaT supervisor confirmed ethics/consent requirements (`materials.md`, `consent_form.md`).
- [ ] Researcher contact details added to `consent_form.md` and verified inside each Google Form.
- [ ] Do **not** collect data until clearance is confirmed.

## 2. Generate all forms and portal

```bash
make human-eval-stimuli          # if packets not built yet
make human-eval-oauth            # one-time Google sign-in
make human-eval-forms-all        # P002 through P010 (after P001)
make human-eval-forms-extended   # P011 through P020 + portal refresh
```

Outputs (gitignored, researcher machine):

| File | Purpose |
|------|---------|
| `generated/form_links.csv` | Direct form URLs (keep private) |
| `generated/form_registry.json` | Export/scoring metadata (keep private) |
| `generated/participant_portal.html` | **Single public entry page** |
| `generated/randomization_key.csv` | Unblinding key (never share) |

Track assignments in `participant_assignment_template.csv` (optional).

## 3. Verify before hosting

- [ ] Open `participant_portal.html` locally and test codes **P001** through **P020**.
- [ ] Each code opens the correct form (spot-check P001, P010, P020).
- [ ] Form page 1: study overview, consent, instructions present.
- [ ] Forms do **not** require Google sign-in for submission.
- [ ] Spot-check one question block: System A/B/C blinded, ESS grid, optional comment.

## 4. Host the portal (HTTPS)

Upload `generated/participant_portal.html` to one of:

- **Google Sites** (recommended for UMaT): New site → Embed or upload HTML → Publish.
- **Netlify Drop**: drag the HTML file to [app.netlify.com/drop](https://app.netlify.com/drop).
- **GitHub Pages**: commit HTML to a public repo page (only if you are comfortable hosting the redirect map).

Use **HTTPS**. Avoid emailing the HTML file or `file://` links for distributed online collection.

## 5. What to share

| Audience | Share |
|----------|--------|
| Everyone | Hosted portal URL only |
| Each participant (private) | Their code (`P001`, `P002`, …) |
| Researcher only | `form_links.csv`, `randomization_key.csv`, assignment sheet |

Codes are routing labels, not strong passwords. Do not post the code list publicly.

## 6. After responses arrive

```bash
.venv/bin/python eval/human_eval/export_responses.py
.venv/bin/python eval/human_eval/score_responses.py eval/human_eval/responses/P001_completed.csv
```

## 7. If you add or regenerate forms

```bash
make human-eval-portal   # rebuild portal after form_links.csv changes
```

Re-upload the updated `participant_portal.html` to your host.
