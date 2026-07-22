"""Run Google OAuth once and save token.json for Forms API scripts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from eval.human_eval.google_auth import DEFAULT_CREDENTIALS_PATH, DEFAULT_TOKEN_PATH, get_credentials

DEFAULT_DOWNLOADED_CREDENTIALS = (
    Path.home()
    / "Documents/client_secret_720894942769-qlm75uf82ec5lbslcv2m3r8tidrh6t2t.apps.googleusercontent.com.json"
)
GCP_CREDENTIALS_URL = (
    "https://console.cloud.google.com/apis/credentials"
    "?project=_&supportedpurview=project"
)


def _write_credentials_from_env(path: Path) -> bool:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return False
    project_id = os.environ.get("GOOGLE_OAUTH_PROJECT_ID", "msha-safety-agent").strip()
    payload = {
        "installed": {
            "client_id": client_id,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
        }
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote OAuth client file from environment variables: {path}")
    return True


def _import_downloaded_credentials(source: Path, dest: Path) -> bool:
    if not source.exists():
        return False
    shutil.copy2(source, dest)
    print(f"Copied OAuth credentials: {source} -> {dest}")
    return True


def _open_browser(url: str) -> None:
    for command in (
        ["xdg-open", url],
        ["gio", "open", url],
        ["wslview", url],
    ):
        if shutil.which(command[0]):
            try:
                subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Opened browser: {url}")
                return
            except OSError:
                continue
    print(f"Open this URL in your browser:\n{url}")


def _print_setup_steps() -> None:
    print(
        "\nGoogle OAuth setup (one time):\n"
        "1. Create or select a Google Cloud project.\n"
        "2. Enable Google Forms API and Google Drive API.\n"
        "3. Configure the OAuth consent screen.\n"
        "4. Create OAuth client ID: Application type = Desktop app.\n"
        "5. Download the JSON and save it as:\n"
        f"   {DEFAULT_CREDENTIALS_PATH}\n"
        "   Or set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.\n"
        "6. Re-run: make human-eval-oauth\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Authorize Google Forms API access.")
    parser.add_argument(
        "--credentials-source",
        type=Path,
        help="Path to downloaded Google OAuth JSON (copied to eval/human_eval/credentials.json).",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Use manual URL + authorization code flow (no local callback server).",
    )
    parser.add_argument(
        "--open-console",
        action="store_true",
        help="Open Google Cloud credentials page before checking for credentials.json.",
    )
    args = parser.parse_args()

    if args.open_console:
        _open_browser(GCP_CREDENTIALS_URL)

    if args.credentials_source:
        _import_downloaded_credentials(args.credentials_source, DEFAULT_CREDENTIALS_PATH)
    elif not DEFAULT_CREDENTIALS_PATH.exists() and DEFAULT_DOWNLOADED_CREDENTIALS.exists():
        _import_downloaded_credentials(DEFAULT_DOWNLOADED_CREDENTIALS, DEFAULT_CREDENTIALS_PATH)
    elif not DEFAULT_CREDENTIALS_PATH.exists():
        _write_credentials_from_env(DEFAULT_CREDENTIALS_PATH)

    if not DEFAULT_CREDENTIALS_PATH.exists():
        _print_setup_steps()
        _open_browser(GCP_CREDENTIALS_URL)
        print(f"Missing credentials file: {DEFAULT_CREDENTIALS_PATH}")
        return 1

    creds = get_credentials(use_console=args.console)
    print(f"OAuth complete. Saved token: {DEFAULT_TOKEN_PATH}")
    print(f"Authorized Google account: {creds.client_id}")
    print("Next: make human-eval-forms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
