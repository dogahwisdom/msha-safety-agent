"""Build a single-entry participant portal from form_links.csv."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.human_eval.form_data import form_title

GENERATED_DIR = Path(__file__).resolve().parent / "generated"
DEFAULT_LINKS_PATH = GENERATED_DIR / "form_links.csv"
DEFAULT_OUTPUT_PATH = GENERATED_DIR / "participant_portal.html"


def load_form_links(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run eval/human_eval/generate_forms.py first."
        )
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    links = {row["participant_id"].strip().upper(): row["form_url"].strip() for row in rows}
    if not links:
        raise ValueError(f"No participant links found in {path}")
    return links


def build_portal_html(links: dict[str, str]) -> str:
    payload = json.dumps(links, indent=2)
    study_title = form_title("P001")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{study_title} | Participant Portal</title>
  <style>
    :root {{
      --bg: #f4f6f9;
      --card: #ffffff;
      --text: #1f2937;
      --muted: #6b7280;
      --accent: #334155;
      --accent-hover: #1e293b;
      --accent-soft: #f8fafc;
      --border: #e2e8f0;
      --error: #b91c1c;
      --shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      color: var(--text);
      background: linear-gradient(180deg, #eef2f7 0%, var(--bg) 220px);
    }}
    .wrap {{
      max-width: 720px;
      margin: 0 auto;
      padding: 48px 20px 64px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .hero {{
      padding: 32px 32px 24px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(135deg, #334155 0%, #475569 100%);
      color: #fff;
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 1.65rem;
      line-height: 1.25;
      font-weight: 700;
    }}
    .hero p {{
      margin: 0;
      color: rgba(255, 255, 255, 0.92);
      line-height: 1.6;
      font-size: 0.98rem;
    }}
    .body {{
      padding: 28px 32px 32px;
    }}
    .meta {{
      display: grid;
      gap: 12px;
      margin-bottom: 28px;
      padding: 16px 18px;
      border-radius: 12px;
      background: var(--accent-soft);
      border: 1px solid var(--border);
      font-size: 0.95rem;
      line-height: 1.55;
    }}
    .meta strong {{
      display: block;
      margin-bottom: 4px;
      color: var(--accent);
      font-size: 0.82rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    label {{
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      font-size: 0.95rem;
    }}
    .hint {{
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.5;
    }}
    input[type="text"] {{
      width: 100%;
      padding: 14px 16px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
      font-size: 1rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }}
    input[type="text"]:focus {{
      outline: 2px solid rgba(51, 65, 85, 0.25);
      border-color: var(--accent);
    }}
    button {{
      margin-top: 16px;
      width: 100%;
      border: 0;
      border-radius: 10px;
      padding: 14px 18px;
      background: var(--accent);
      color: #fff;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
    }}
    button:hover {{
      background: var(--accent-hover);
    }}
    .error {{
      display: none;
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 10px;
      background: #fef2f2;
      color: var(--error);
      border: 1px solid #fecaca;
      font-size: 0.92rem;
      line-height: 1.45;
    }}
    .error.visible {{
      display: block;
    }}
    footer {{
      margin-top: 18px;
      text-align: center;
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.5;
    }}
    @media (max-width: 640px) {{
      .hero, .body {{ padding-left: 20px; padding-right: 20px; }}
      .hero h1 {{ font-size: 1.35rem; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="hero">
        <h1>{study_title}</h1>
        <p>University of Mines and Technology (UMaT). Enter the participant code provided by the researcher to begin your survey.</p>
      </div>
      <div class="body">
        <div class="meta">
          <div>
            <strong>Estimated time</strong>
            45 to 60 minutes. You may pause and return later.
          </div>
          <div>
            <strong>What you will do</strong>
            Read mine safety questions and rate system-generated explanations from three blinded systems (A, B, and C).
          </div>
          <div>
            <strong>Confidentiality</strong>
            Participation is voluntary. Do not share your participant code with others.
          </div>
        </div>
        <form id="portal-form" novalidate>
          <label for="participant-id">Participant code</label>
          <p class="hint">Example format: P001. Codes are case insensitive.</p>
          <input id="participant-id" name="participant-id" type="text" autocomplete="off" placeholder="P001" required>
          <button type="submit">Continue to survey</button>
          <p id="error" class="error" role="alert"></p>
        </form>
      </div>
    </div>
    <footer>
      Research use only. If you did not receive a code from the study team, do not proceed.
    </footer>
  </div>
  <script>
    const FORM_LINKS = {payload};

    const form = document.getElementById("portal-form");
    const input = document.getElementById("participant-id");
    const error = document.getElementById("error");

    function normalizeCode(value) {{
      return value.trim().toUpperCase();
    }}

    function showError(message) {{
      error.textContent = message;
      error.classList.add("visible");
    }}

    function clearError() {{
      error.textContent = "";
      error.classList.remove("visible");
    }}

    form.addEventListener("submit", (event) => {{
      event.preventDefault();
      clearError();
      const code = normalizeCode(input.value);
      if (!code) {{
        showError("Enter the participant code provided by the researcher.");
        return;
      }}
      if (!/^P\\d{{3}}$/.test(code)) {{
        showError("Use the format P001 (letter P followed by three digits).");
        return;
      }}
      const target = FORM_LINKS[code];
      if (!target) {{
        showError("That participant code is not active. Check the code and try again, or contact the study team.");
        return;
      }}
      window.location.href = target;
    }});
  </script>
</body>
</html>
"""


def write_portal(
    *,
    links_path: Path = DEFAULT_LINKS_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> Path:
    links = load_form_links(links_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_portal_html(links), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--links",
        type=Path,
        default=DEFAULT_LINKS_PATH,
        help="CSV with participant_id and form_url columns.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output HTML path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = write_portal(links_path=args.links, output_path=args.output)
    print(f"Wrote {out}")
    print(f"Active participant codes: {', '.join(sorted(load_form_links(args.links)))}")


if __name__ == "__main__":
    main()
