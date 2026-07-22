"""OAuth helpers for Google Forms API scripts."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

FORMS_SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

DEFAULT_CREDENTIALS_PATH = Path(__file__).resolve().parent / "credentials.json"
DEFAULT_TOKEN_PATH = Path(__file__).resolve().parent / "token.json"


def get_credentials(
    *,
    credentials_path: Path = DEFAULT_CREDENTIALS_PATH,
    token_path: Path = DEFAULT_TOKEN_PATH,
    scopes: list[str] | None = None,
    use_console: bool = False,
) -> Credentials:
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google OAuth credentials not found at {credentials_path}. "
            "See docs/REPRODUCTION.md (Google Forms API setup)."
        )
    use_scopes = scopes or FORMS_SCOPES
    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), use_scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), use_scopes)
            if use_console:
                flow.redirect_uri = "http://localhost:8080/"
                auth_url, _ = flow.authorization_url(
                    access_type="offline",
                    prompt="consent",
                )
                print("Open this URL in your browser, sign in, then paste the redirect URL here:")
                print(auth_url)
                redirect_response = input("Redirect URL: ").strip()
                flow.fetch_token(authorization_response=redirect_response)
                creds = flow.credentials
            else:
                creds = flow.run_local_server(
                    host="localhost",
                    port=8080,
                    open_browser=True,
                    authorization_prompt_message=(
                        "\nSign-in URL (also opening in your browser):\n{url}\n\n"
                        "If Google shows 'app isn't verified': click Advanced, then continue.\n"
                        "Use only this tab. Close any other Google 400 error tabs.\n"
                    ),
                    access_type="offline",
                    prompt="consent",
                )
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_forms_service(creds: Credentials):
    return build("forms", "v1", credentials=creds, cache_discovery=False)
