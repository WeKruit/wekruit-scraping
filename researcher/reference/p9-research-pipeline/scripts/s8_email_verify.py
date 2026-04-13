"""
S8: Email Verification via NeverBounce
Verifies collected emails and tags them as valid/invalid/catchall.

Usage:
  python scripts/s8_email_verify.py --input data/merged_profiles.jsonl --output data/verified.jsonl
"""
import argparse, json, os, sys, time
from pathlib import Path
import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATA_DIR, NEVERBOUNCE_API_KEY

NB_URL = "https://api.neverbounce.com/v4/single/check"
STATUS_MAP = {0: "valid", 1: "invalid", 2: "disposable", 3: "catchall", 4: "unknown"}


def verify_email(email: str) -> dict:
    if not NEVERBOUNCE_API_KEY:
        return {"email": email, "status": "skipped", "reason": "no_api_key"}
    try:
        r = requests.get(NB_URL, params={"key": NEVERBOUNCE_API_KEY, "email": email}, timeout=30)
        r.raise_for_status()
        data = r.json()
        return {"email": email, "status": STATUS_MAP.get(data.get("result"), "unknown"),
                "nb_response": data}
    except Exception as e:
        return {"email": email, "status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="S8: Email verification")
    parser.add_argument("--input", type=str, default=f"{DATA_DIR}/merged_profiles.jsonl")
    parser.add_argument("--output", type=str, default=f"{DATA_DIR}/verified.jsonl")
    args = parser.parse_args()

    profiles = [json.loads(l) for l in open(args.input) if l.strip()]
    all_emails = set()
    for p in profiles:
        for e in p.get("emails", []):
            email = e.get("email") if isinstance(e, dict) else e
            if email: all_emails.add(email)

    print(f"[S8] Verifying {len(all_emails)} unique emails")

    results = {}
    for email in tqdm(all_emails, desc="Verify"):
        results[email] = verify_email(email)
        time.sleep(0.2)

    # Update profiles
    for p in profiles:
        for e in p.get("emails", []):
            email = e.get("email") if isinstance(e, dict) else e
            if email and email in results:
                if isinstance(e, dict):
                    e["verified"] = results[email]["status"] == "valid"
                    e["verification_status"] = results[email]["status"]

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        for p in profiles:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    valid = sum(1 for r in results.values() if r["status"] == "valid")
    print(f"[S8] Valid: {valid}/{len(all_emails)} → {args.output}")


if __name__ == "__main__":
    main()
