#!/usr/bin/env python3
"""
Upload all hackathon CSVs as tabs in one Google Sheet.
First run will open a browser for Google login.

Usage:
    python3 upload_to_sheets.py
"""

import csv, os, glob, time, sys

try:
    import gspread
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("Install deps: pip3 install gspread google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
TOKEN_FILE = os.path.expanduser("~/.config/gspread/token.json")
CREDS_FILE = os.path.expanduser("~/.config/gspread/credentials.json")
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "by_hackathon")
SHEET_TITLE = "Devpost Hackathons — All Data"


def get_creds():
    """Get Google credentials, prompting browser login if needed."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                print(f"\nNeed OAuth credentials file at: {CREDS_FILE}")
                print("Get it from: https://console.cloud.google.com/apis/credentials")
                print("  1. Create OAuth 2.0 Client ID (Desktop app)")
                print("  2. Download JSON -> save as credentials.json")
                print(f"  3. Move to {CREDS_FILE}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def main():
    csvs = sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))
    if not csvs:
        print(f"No CSVs found in {CSV_DIR}")
        sys.exit(1)

    print(f"Found {len(csvs)} CSVs to upload")
    print("Authenticating with Google...")
    creds = get_creds()
    gc = gspread.authorize(creds)

    # Create spreadsheet
    print(f'Creating spreadsheet: "{SHEET_TITLE}"')
    sh = gc.create(SHEET_TITLE)
    print(f"  URL: {sh.url}")

    # Make it accessible
    sh.share("", perm_type="anyone", role="reader")
    print("  Shared as public read-only")

    for i, csv_path in enumerate(csvs):
        name = os.path.basename(csv_path).replace(".csv", "")
        # Sheet tab names max 100 chars
        tab_name = name[:100]

        print(f"  [{i+1}/{len(csvs)}] {tab_name}...", end=" ", flush=True)

        # Read CSV
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        if not rows:
            print("empty, skipped")
            continue

        # Google Sheets limit: 10M cells per spreadsheet
        # Trim description to keep cell size manageable
        desc_idx = rows[0].index("description") if "description" in rows[0] else -1
        if desc_idx >= 0:
            for row in rows[1:]:
                if len(row) > desc_idx and len(row[desc_idx]) > 1000:
                    row[desc_idx] = row[desc_idx][:1000] + "..."

        # Create worksheet
        try:
            if i == 0:
                ws = sh.sheet1
                ws.update_title(tab_name)
            else:
                ws = sh.add_worksheet(title=tab_name, rows=len(rows), cols=len(rows[0]))

            ws.update(rows, value_input_option="RAW")
            print(f"{len(rows)-1} rows")
        except Exception as e:
            print(f"ERROR: {e}")

        # Rate limit: 60 requests/min for Sheets API
        time.sleep(2)

    print(f"\nDone! Spreadsheet URL: {sh.url}")


if __name__ == "__main__":
    main()
