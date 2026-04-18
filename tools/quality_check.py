#!/usr/bin/env python3
"""Scan converted QMD files for leaked PMWiki markup.

Usage:
    uv run python tools/quality_check.py              # scan all pages
    uv run python tools/quality_check.py --page Class.14
    uv run python tools/quality_check.py --strict     # exit 1 on critical/high
"""

import argparse
import json
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SITE_DIR = REPO_ROOT / "site"
WIKI_DIR = REPO_ROOT / "pmwiki_data" / "wiki.d"
SPEC_PATH = REPO_ROOT / "agents" / "pmwiki_quality_check.json"

SEVERITY_ORDER = ["critical", "high", "medium", "low"]

# Map QMD output path back to wiki page name
QMD_TO_WIKI = {
    "class": lambda stem: f"Class.{stem.replace('class-', '')}",
    "definitions": lambda stem: f"Definition.{stem.title()}",
    "flex": lambda stem: f"Flex.{stem.replace('flex-', '')}",
}

CODE_FENCE_RE = re.compile(r'```[\s\S]*?```|`[^`\n]+`', re.DOTALL)
MATH_RE = re.compile(
    r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}|\$\$[\s\S]*?\$\$|\$[^\$\n]+?\$',
    re.DOTALL,
)


def _mask_regions(text: str) -> str:
    """Replace code fences and math with spaces, preserving newlines to keep line indices correct."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = CODE_FENCE_RE.sub(blank, text)
    text = MATH_RE.sub(blank, text)
    return text


def _decode_wiki_page(wiki_path: Path) -> str:
    raw = wiki_path.read_text(encoding="utf-8", errors="replace")
    for line in raw.split("\n"):
        if line.startswith("text="):
            return urllib.parse.unquote(line[5:])
    return ""


def _find_wiki_source(wiki_text: str, qmd_snippet: str) -> str:
    """Return the wiki line most likely to be the source of a QMD snippet."""
    # Use up to 20 chars of the snippet as a search key
    key = qmd_snippet.strip()[:20].lower()
    for line in wiki_text.split("\n"):
        if key and key[:10] in line.lower():
            return line.rstrip()
    return "(source line not found)"


def _wiki_path_for_qmd(qmd_path: Path) -> Path | None:
    parts = qmd_path.relative_to(SITE_DIR).parts
    if len(parts) < 2:
        return None
    folder, filename = parts[0], parts[1]
    stem = Path(filename).stem
    name_fn = QMD_TO_WIKI.get(folder)
    if not name_fn:
        return None
    wiki_name = name_fn(stem)
    candidate = WIKI_DIR / wiki_name
    return candidate if candidate.exists() else None


def scan_file(qmd_path: Path, checks: list) -> list:
    """Return list of findings dicts for a single QMD file."""
    text = qmd_path.read_text(encoding="utf-8", errors="replace")
    masked = _mask_regions(text)
    lines = text.split("\n")
    masked_lines = masked.split("\n")

    wiki_path = _wiki_path_for_qmd(qmd_path)
    wiki_text = _decode_wiki_page(wiki_path) if wiki_path else ""

    findings = []

    for check in checks:
        cid = check["id"]
        pattern = check.get("pattern")
        severity = check["severity"]

        # G17: count-based check
        if cid == "G17":
            opens = text.count("<details>")
            closes = text.count("</details>")
            if opens != closes:
                findings.append({
                    "check_id": cid,
                    "severity": severity,
                    "file": str(qmd_path.relative_to(REPO_ROOT)),
                    "line_number": None,
                    "qmd_text": f"<details> count={opens}, </details> count={closes}",
                    "wiki_source": "",
                    "description": check["description"],
                })
            continue

        if not pattern:
            continue

        flags = re.MULTILINE if "MULTILINE" in check.get("flags", "") else 0
        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            continue

        for i, (line, mline) in enumerate(zip(lines, masked_lines), start=1):
            if compiled.search(mline):
                wiki_src = _find_wiki_source(wiki_text, line) if wiki_text else ""
                findings.append({
                    "check_id": cid,
                    "severity": severity,
                    "file": str(qmd_path.relative_to(REPO_ROOT)),
                    "line_number": i,
                    "qmd_text": line.rstrip(),
                    "wiki_source": wiki_src,
                    "description": check["description"],
                })

    return findings


def collect_qmd_files(page_filter: str | None) -> list[Path]:
    files = []
    for folder in ["class", "definitions", "flex"]:
        folder_path = SITE_DIR / folder
        if folder_path.exists():
            files.extend(sorted(folder_path.glob("*.qmd")))

    if page_filter:
        group, _, page = page_filter.partition(".")
        if group == "Class":
            target = f"class-{page}.qmd"
            folder = "class"
        elif group == "Flex":
            target = f"flex-{page}.qmd"
            folder = "flex"
        elif group == "Definition":
            target = f"{page.lower()}.qmd"
            folder = "definitions"
        else:
            return []
        matched = SITE_DIR / folder / target
        return [matched] if matched.exists() else []

    return files


def group_by_severity(findings: list) -> dict:
    grouped = {s: [] for s in SEVERITY_ORDER}
    for f in findings:
        s = f["severity"]
        if s in grouped:
            grouped[s].append(f)
    return grouped


def write_report(findings: list, pages_scanned: int, out_path: Path):
    grouped = group_by_severity(findings)
    lines = [
        "# Quality Check Report",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"Pages scanned: {pages_scanned}  ",
        f"Total findings: {len(findings)}",
        f"",
        "## Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]
    for s in SEVERITY_ORDER:
        lines.append(f"| {s.capitalize()} | {len(grouped[s])} |")

    for severity in SEVERITY_ORDER:
        items = grouped[severity]
        if not items:
            continue
        lines.append(f"\n## {severity.capitalize()} Issues\n")
        for f in items:
            loc = f"line {f['line_number']}" if f['line_number'] else "file-level"
            lines.append(f"### [{f['check_id']}] {f['file']} — {loc}")
            lines.append(f"**Check**: {f['description']}  ")
            lines.append(f"**QMD**: `{f['qmd_text'][:120]}`  ")
            if f.get("wiki_source"):
                lines.append(f"**Wiki source**: `{f['wiki_source'][:120]}`  ")
            lines.append("")

    out_path.write_text("\n".join(lines))
    print(f"Report written to: {out_path.relative_to(REPO_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Scan QMD files for leaked PMWiki markup")
    parser.add_argument("--page", help="Check a single page (e.g. Class.14)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any critical/high issues found")
    args = parser.parse_args()

    spec = json.loads(SPEC_PATH.read_text())
    checks = spec["checks"]["leak_patterns"]

    files = collect_qmd_files(args.page)
    if not files:
        print("No QMD files found. Run: uv run python tools/pmwiki_to_quarto.py first.")
        sys.exit(1)

    all_findings = []
    for qmd in files:
        findings = scan_file(qmd, checks)
        all_findings.extend(findings)
        if findings:
            print(f"  {qmd.relative_to(REPO_ROOT)}: {len(findings)} finding(s)")

    write_report(all_findings, len(files), REPO_ROOT / "quality_report.md")

    blocking = [f for f in all_findings if f["severity"] in ("critical", "high")]
    print(f"\nTotal: {len(all_findings)} findings ({len(blocking)} critical/high)")

    if args.strict and blocking:
        sys.exit(1)


if __name__ == "__main__":
    main()
