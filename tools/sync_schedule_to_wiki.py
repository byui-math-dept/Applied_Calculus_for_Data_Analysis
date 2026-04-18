#!/usr/bin/env python3
"""Push schedule_config.yml dates to PMWiki flat files and upload via SFTP.

Creates or updates Schedule.YYYYMMDD pages in pmwiki_data/wiki.d/ to match
the sessions defined in schedule_config.yml, then uploads changed files to
the server.

Usage:
    uv run python tools/sync_schedule_to_wiki.py --dry-run   # preview only
    uv run python tools/sync_schedule_to_wiki.py             # write + upload
"""

import argparse
import os
import sys
import time
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
CONFIG_PATH = REPO_ROOT / "schedule_config.yml"
WIKI_DIR = REPO_ROOT / "pmwiki_data" / "wiki.d"

WEEKDAY_MAP = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

SESSION_LABELS = {
    "review":  "Review Day",
    "project": "Project Work Day",
    "testing": "Testing Day",
    "holiday": "(No Class)",
}


# ---------------------------------------------------------------------------
# Schedule page content generators
# ---------------------------------------------------------------------------

def _class_page_content(class_num: int, next_num: int | None) -> str:
    next_line = f"(:next: {next_num}:)" if next_num else "(:next: :)"
    return (
        f"(:today: {class_num}:)\n"
        f"{next_line}\n"
        f"'+Today is Day {{$:today}}+'\n\n"
        f"(:include Prep.{{$:today}}:)\n"
        f"(:include Class.{{$:today}}:)\n"
        f"(:include Link.BetweenClassSessions Date={{$:Name}}:)\n"
    )


def _flex_page_content(flex_num: int) -> str:
    return f"(:include Flex.{flex_num}:)\n"


def _project_page_content() -> str:
    return "Today is a Project Work Day. Come work on your project or Knewton Alta. I'll be in class to answer questions.\n"


def _holiday_page_content(name: str) -> str:
    return f"No class today — {name}.\n"


def session_content(session: str, next_class_num: int | None, holiday_name: str = "") -> str:
    if session.startswith("class-"):
        num = int(session.split("-")[1])
        return _class_page_content(num, next_class_num)
    elif session.startswith("flex-"):
        num = int(session.split("-")[1])
        return _flex_page_content(num)
    elif session == "project":
        return _project_page_content()
    elif session == "holiday":
        return _holiday_page_content(holiday_name)
    else:
        label = SESSION_LABELS.get(session, session.title())
        return f"{label}\n"


# ---------------------------------------------------------------------------
# PMWiki flat file writing
# ---------------------------------------------------------------------------

def _encode_pmwiki(text: str) -> str:
    """URL-encode text for PMWiki flat file format."""
    return urllib.parse.quote(text, safe=" \t!#$&'()*+,-./:;=?@[]^_`{|}~")


def write_wiki_flat_file(wiki_dir: Path, page_name: str, content: str, dry_run: bool) -> bool:
    """Write a PMWiki flat file. Returns True if file was created/changed."""
    path = wiki_dir / page_name
    now = int(time.time())
    encoded = _encode_pmwiki(content)

    flat = (
        f"version=pmwiki-2.3.0 ordered=1 urlencoded=1\n"
        f"agent=sync_schedule_to_wiki.py\n"
        f"author=schedule-sync\n"
        f"charset=UTF-8\n"
        f"csum=schedule sync\n"
        f"host=local\n"
        f"name={page_name}\n"
        f"rev=1\n"
        f"targets=\n"
        f"time={now}\n"
        f"text={encoded}\n"
    )

    if path.exists():
        existing = path.read_text(errors="replace")
        # Compare only the text= line to avoid timestamp churn
        existing_text = next((l for l in existing.split("\n") if l.startswith("text=")), "")
        new_text = f"text={encoded}"
        if existing_text == new_text:
            return False  # no change

    if dry_run:
        print(f"  [dry-run] would write: {page_name}")
        return True

    path.write_text(flat, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# SFTP upload
# ---------------------------------------------------------------------------

def upload_changed(changed_pages: list[str], dry_run: bool):
    if not changed_pages:
        print("No pages changed — nothing to upload.")
        return
    if dry_run:
        print(f"\n[dry-run] Would upload {len(changed_pages)} file(s) via SFTP.")
        return

    try:
        import paramiko
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        print("WARNING: paramiko not available — skipping SFTP upload. Run: uv sync")
        return

    host = os.environ.get("SFTP_HOST")
    port = int(os.environ.get("SFTP_PORT", 22))
    user = os.environ.get("SFTP_USERNAME")
    password = os.environ.get("SFTP_PASSWORD")
    remote_base = os.environ.get("SFTP_REMOTE_BASE", "")

    if not all([host, user, password]):
        print("WARNING: SFTP credentials missing in .env — skipping upload.")
        return

    remote_wiki = f"{remote_base}/wiki.d"

    transport = paramiko.Transport((host, port))
    transport.connect(username=user, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        for page_name in changed_pages:
            local_path = WIKI_DIR / page_name
            remote_path = f"{remote_wiki}/{page_name}"
            sftp.put(str(local_path), remote_path)
            print(f"  uploaded: {page_name}")
    finally:
        sftp.close()
        transport.close()

    print(f"Uploaded {len(changed_pages)} file(s) to {host}.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_calendar(config: dict) -> list[dict]:
    start = date.fromisoformat(config["semester"]["start"])
    end   = date.fromisoformat(config["semester"]["end"])
    class_days = {WEEKDAY_MAP[d] for d in config["semester"]["class_days"]}
    holidays = {date.fromisoformat(h["date"]): h["name"] for h in config.get("holidays", [])}
    sessions = config["sessions"]

    calendar = []
    session_idx = 0
    current = start

    while current <= end and session_idx < len(sessions):
        if current.weekday() not in class_days:
            current += timedelta(days=1)
            continue

        if current in holidays:
            calendar.append({"date": current, "session": "holiday", "holiday_name": holidays[current]})
            current += timedelta(days=1)
            continue

        calendar.append({"date": current, "session": sessions[session_idx]})
        session_idx += 1
        current += timedelta(days=1)

    return calendar


def next_class_num(calendar: list[dict], from_idx: int) -> int | None:
    """Return the class number of the next class-N entry after from_idx."""
    for entry in calendar[from_idx + 1:]:
        if entry["session"].startswith("class-"):
            return int(entry["session"].split("-")[1])
    return None


def main():
    parser = argparse.ArgumentParser(description="Sync schedule_config.yml to PMWiki flat files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--no-upload", action="store_true", help="Write local files but skip SFTP")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        sys.exit(f"ERROR: {CONFIG_PATH} not found.")
    if not WIKI_DIR.exists():
        sys.exit(f"ERROR: {WIKI_DIR} not found. Run: uv run pull_wiki.py first.")

    config = yaml.safe_load(CONFIG_PATH.read_text())
    calendar = build_calendar(config)

    print(f"Processing {len(calendar)} schedule entries...")
    changed = []

    for i, entry in enumerate(calendar):
        d = entry["date"]
        session = entry["session"]
        page_name = f"Schedule.{d.strftime('%Y%m%d')}"
        next_num = next_class_num(calendar, i) if session.startswith("class-") else None
        content = session_content(session, next_num, entry.get("holiday_name", ""))

        if write_wiki_flat_file(WIKI_DIR, page_name, content, args.dry_run):
            changed.append(page_name)
            if not args.dry_run:
                print(f"  wrote: {page_name}  ({session})")

    print(f"\n{len(changed)} file(s) {'would be ' if args.dry_run else ''}updated.")

    if not args.no_upload:
        upload_changed(changed, args.dry_run)
    else:
        print("Skipping SFTP upload (--no-upload).")


if __name__ == "__main__":
    main()
