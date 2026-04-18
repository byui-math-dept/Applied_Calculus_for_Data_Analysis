#!/usr/bin/env python3
"""Convert PMWiki flat files from pmwiki_data/ to a Quarto website in site/.

Usage:
    uv run python tools/pmwiki_to_quarto.py              # full conversion
    uv run python tools/pmwiki_to_quarto.py --page Class.5   # single page
    uv run python tools/pmwiki_to_quarto.py --dry-run    # show what would change
"""

import argparse
import re
import shutil
import urllib.parse
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "pmwiki_data" / "wiki.d"
UPLOADS_DIR = REPO_ROOT / "pmwiki_data" / "uploads"
SITE_DIR = REPO_ROOT / "site"

# Groups to convert and their output folders
CONVERT_GROUPS = {
    "Class": "class",
    "Definition": "definitions",
    "Flex": "flex",
}

# ---------------------------------------------------------------------------
# PMWiki file decoding
# ---------------------------------------------------------------------------

def decode_pmwiki_file(file_path: Path) -> dict:
    """Read a PMWiki flat file and return decoded metadata + page text."""
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    lines = raw.split("\n")

    meta = {}
    text_line = ""
    for line in lines:
        if line.startswith("text="):
            text_line = line
            break
        if "=" in line:
            key, _, val = line.partition("=")
            meta[key.strip()] = val.strip()

    text = urllib.parse.unquote(text_line[5:]) if text_line else ""
    return {
        "name": meta.get("name", file_path.name),
        "text": text,
        "mtime": meta.get("time", ""),
        "rev": meta.get("rev", "0"),
    }


# ---------------------------------------------------------------------------
# Math placeholder system
# ---------------------------------------------------------------------------

MATH_PLACEHOLDER = "XXMATHXX"

# Patterns ordered longest/most-specific first
_MATH_RE = re.compile(
    r'|'.join([
        r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}',
        r'\$\$[\s\S]*?\$\$',
        r'\$[^\$\n]+?\$',
    ]),
    flags=re.DOTALL,
)

def extract_math(text: str) -> tuple[str, dict]:
    """Replace all math expressions with placeholders. Returns (text, store)."""
    store = {}
    idx = [0]

    def replacer(m):
        key = f"{MATH_PLACEHOLDER}{idx[0]}{MATH_PLACEHOLDER}"
        store[key] = m.group(0)
        idx[0] += 1
        return key

    return _MATH_RE.sub(replacer, text), store


def restore_math(text: str, store: dict) -> str:
    for key, val in store.items():
        text = text.replace(key, val)
    return text


# ---------------------------------------------------------------------------
# Block-level conversions (applied before inline rules)
# ---------------------------------------------------------------------------

def strip_directives(text: str) -> str:
    """Remove server-side PMWiki directives that have no static equivalent."""
    # (:if false:)...(:if:) — hidden conditional blocks
    text = re.sub(r'\(:if false:\)[\s\S]*?\(:if:\)', '', text)
    # (:pagelist ...:) — dynamic page lists
    text = re.sub(r'\(:pagelist[^:]*:\)', '', text)
    # (:Summary:...:) — metadata
    text = re.sub(r'\(:Summary:[^:]*:\)', '', text)
    # (:attachlist:) — dynamic attachment list (replaced in caller with static list)
    text = re.sub(r'\(:attachlist:\)', '<!-- attachlist -->', text)
    # (:title ...:) — page title override
    text = re.sub(r'\(:title[^:]*:\)', '', text)
    # (:include ...:) — server-side page include (drop with comment)
    text = re.sub(r'\(:include\s+([^:]+):\)', lambda m: f'<!-- include: {m.group(1).strip()} -->', text)
    # (:comment ...:) — server-side comment (strip entirely)
    text = re.sub(r'\(:comment[\s\S]*?:\)', '', text)
    # (:if:) remaining tags
    text = re.sub(r'\(:if[^:]*:\)', '', text)
    # (:table:), (:cell:), (:tableend:) — layout tables; cells separated by blank lines
    text = re.sub(r'\(:table[^:]*:\)', '', text)
    text = re.sub(r'\(:cell[^:]*:\)', '\n\n', text)
    text = re.sub(r'\(:tableend:\)', '', text)
    return text


def convert_code_blocks(text: str) -> str:
    """Convert PMWiki [@...@] code blocks to fenced or inline code.

    (:code:)[@...@](:codeend:) → fenced block.
    Bare [@word@] in running text (no newline inside) → `inline`.
    """
    def block_replacer(m):
        lang = "r" if any(kw in m.group(1) for kw in ["function", "<-", "library", "#"]) else ""
        return f"\n```{lang}\n{m.group(1).strip()}\n```\n"

    # Named block form first: (:code:)[@...@](:codeend:)
    text = re.sub(r'\(:code[^:]*:\)\[@([\s\S]*?)@\]\(:codeend:\)', block_replacer, text)
    # Remaining multi-line [@...@] → fenced block
    text = re.sub(r'\[@([\s\S]*?\n[\s\S]*?)@\]', block_replacer, text)
    # Single-line [@word@] in prose → inline code
    text = re.sub(r'\[@([^\n@]+?)@\]', lambda m: f'`{m.group(1).strip()}`', text)
    return text


def convert_toggle_blocks(text: str) -> str:
    """Convert >>toggle<< ... >>indent<< content >><< to <details>.

    PMWiki uses one >>indent<< / >>toggle<< per block; >>indent<< is closed by
    >><<, and >>toggle<< is implicitly closed by (:noteend:). So we only need
    to match a single >>><< after the indent body.
    """
    def toggle_with_indent(m):
        title = m.group(1).strip() or "Show"
        content = m.group(2).strip()
        return f"\n<details>\n<summary>{title}</summary>\n\n{content}\n\n</details>\n"

    # Primary pattern: >>toggle<< TITLE >>indent<< CONTENT >><<
    text = re.sub(
        r'>>toggle<<\s*\n(.*?)\n>>indent<<\s*\n([\s\S]*?)\n>><< *',
        toggle_with_indent,
        text
    )
    # Fallback: toggle without indent div
    def toggle_simple(m):
        inner = m.group(1).strip()
        lines = inner.split('\n', 1)
        title = lines[0].strip() if lines else "Show"
        content = lines[1].strip() if len(lines) > 1 else ""
        return f"\n<details>\n<summary>{title}</summary>\n\n{content}\n\n</details>\n"

    text = re.sub(
        r'>>toggle<<\s*\n([\s\S]*?)\n>><< *',
        toggle_simple,
        text
    )
    return text


def convert_note_blocks(text: str) -> str:
    """Strip (:note:)...(:noteend:) wrappers — content (already <details>) is kept as-is."""
    return re.sub(r'\(:note:\)([\s\S]*?)\(:noteend:\)', lambda m: '\n' + m.group(1).strip() + '\n', text)


def convert_pipe_tables(text: str) -> str:
    """Convert PMWiki ||...|| pipe tables to Markdown tables."""
    lines = text.split('\n')
    out = []
    table_rows = []

    def flush_table(rows):
        if not rows:
            return []
        result = []
        header_sep_inserted = False
        for i, (is_header, cells) in enumerate(rows):
            row_md = '| ' + ' | '.join(cells) + ' |'
            result.append(row_md)
            if is_header and not header_sep_inserted:
                sep = '| ' + ' | '.join('---' for _ in cells) + ' |'
                result.append(sep)
                header_sep_inserted = True
        return result

    for line in lines:
        if re.match(r'^\|\|', line):
            raw_cells = re.split(r'\|\|', line)
            raw_cells = [c for c in raw_cells if c != '']
            # Skip PMWiki table attribute rows: single cell of the form "key=val ..."
            if len(raw_cells) == 1 and re.match(r'^[\w]+=', raw_cells[0].strip()):
                continue
            is_header_row = False
            cells = []
            for cell in raw_cells:
                if cell.startswith('!'):
                    is_header_row = True
                    cells.append(cell[1:].strip())
                else:
                    cells.append(cell.strip())
            table_rows.append((is_header_row, cells))
        else:
            if table_rows:
                if out and out[-1].strip():
                    out.append('')
                out.extend(flush_table(table_rows))
                out.append('')
                table_rows = []
            out.append(line)

    if table_rows:
        if out and out[-1].strip():
            out.append('')
        out.extend(flush_table(table_rows))
        out.append('')

    return '\n'.join(out)


def convert_div_blocks(text: str) -> str:
    """Convert remaining >>divname<< ... >>><< div blocks."""
    # >>indent<< ... >><<  → blockquote
    def indent_replacer(m):
        lines = m.group(1).strip().split('\n')
        return '\n' + '\n'.join('> ' + l for l in lines) + '\n'

    text = re.sub(r'>>indent<<\s*\n([\s\S]*?)\n>><< *', indent_replacer, text)

    # >>comment<< ... >><<  → drop
    text = re.sub(r'>>comment<<\s*\n[\s\S]*?\n>><< *', '', text)

    # Any remaining >>something<< ... >><<  → drop the div tags, keep content
    text = re.sub(r'>>[a-z]+<<', '', text)
    text = re.sub(r'>><< *', '', text)

    return text


# ---------------------------------------------------------------------------
# Inline conversions
# ---------------------------------------------------------------------------

def _flush_alpha(buf: list) -> str:
    li_tags = '\n'.join(f'  <li>{item}</li>' for item in buf)
    return f'<ol type="a">\n{li_tags}\n</ol>'


def build_link_registry(page_names: list[str]) -> dict[str, str]:
    """Map PMWiki page names to their output QMD paths."""
    registry = {}
    for name in page_names:
        group, _, page = name.partition('.')
        if group == 'Class' and page.isdigit():
            registry[name] = f"class/class-{page}.qmd"
        elif group == 'Definition':
            slug = page.lower().replace(' ', '-')
            registry[name] = f"definitions/{slug}.qmd"
        elif group == 'Flex' and page.isdigit():
            registry[name] = f"flex/flex-{page}.qmd"
        elif group == 'Schedule':
            registry[name] = f"schedule.qmd#{page.lower()}"
    return registry


def convert_inline(text: str, page_group: str, link_registry: dict) -> str:
    """Apply all inline markup conversion rules."""

    # @@monospace@@ → `monospace` (G4)
    text = re.sub(r'@@(.+?)@@', lambda m: f'`{m.group(1)}`', text)

    # {-strikethrough-} → ~~strikethrough~~ (G6)
    text = re.sub(r'\{-(.+?)-\}', lambda m: f'~~{m.group(1)}~~', text)

    # [[text | url]] pipe-style links → [text](url) (G11)
    text = re.sub(
        r'\[\[([^\]|]+?)\s*\|\s*(https?://[^\]]+)\]\]',
        lambda m: f'[{m.group(1).strip()}]({m.group(2).strip()})',
        text,
    )

    # [[#anchorname]] — PMWiki in-page anchor definition → HTML anchor
    text = re.sub(
        r'\[\[#([A-Za-z][A-Za-z0-9_-]*)\]\]',
        lambda m: f'<a id="{m.group(1)}"></a>',
        text,
    )

    # %newwin%[[text -> url]] — external link, new window
    # If display text is itself a URL (same as target), use "site" as label
    def _newwin_link(m):
        display, url = m.group(1).strip(), m.group(2).strip()
        if display.startswith('http'):
            display = 'site'
        return f'[{display}]({url}){{target="_blank"}}'
    text = re.sub(
        r'%newwin%\[\[(.+?) -> (https?://[^\]]+)\]\]',
        _newwin_link,
        text
    )
    # %newwin%[[url]] — bare new-window link
    text = re.sub(
        r'%newwin%\[\[(https?://[^\]]+)\]\]',
        lambda m: f'[{m.group(1)}]({m.group(1)}){{target="_blank"}}',
        text
    )

    # [[text -> url]] — plain external link with display text
    text = re.sub(
        r'\[\[(.+?) -> (https?://[^\]]+)\]\]',
        lambda m: f'[{m.group(1)}]({m.group(2)})',
        text
    )

    # [[http://url]] — bare external link
    text = re.sub(
        r'\[\[(https?://[^\]]+)\]\]',
        lambda m: f'[{m.group(1)}]({m.group(1)})',
        text
    )

    # [[PageGroup.PageName -> display]] or [[PageGroup.PageName]]
    def internal_link(m):
        target = m.group(1).strip()
        display = m.group(2).strip() if m.group(2) else target
        # Strip anchor
        anchor = ''
        if '#' in target:
            target, anchor = target.split('#', 1)
            anchor = f'#{anchor.lower()}'
        path = link_registry.get(target, f"{target.lower().replace('.', '/')}.qmd")
        return f'[{display}]({path}{anchor})'

    text = re.sub(
        r'\[\[([A-Z][a-zA-Z]+\.[^\]|>]+?)(?:\s*->\s*([^\]]+))?\]\]',
        internal_link,
        text
    )

    # Attach: images with size modifier  %width=Npx% or %height=Npx%
    def _attach_sized(m):
        dim_type = m.group(1)   # width or height
        dim_val = m.group(2)    # e.g. 100px
        filename = m.group(3)
        path = f"../assets/uploads/{page_group}/{filename}"
        attr = f'width="{dim_val}"' if dim_type == 'width' else f'height="{dim_val}"'
        return f'![]({path}){{{attr}}}'

    text = re.sub(
        r'%(width|height)=(\d+[a-z]*)%\s*Attach:(\S+)',
        _attach_sized,
        text,
    )

    # Plain Attach:filename
    text = re.sub(
        r'Attach:(\S+\.(png|jpg|jpeg|gif|svg|PNG|JPG|JPEG))',
        lambda m: f'![](../assets/uploads/{page_group}/{m.group(1)})',
        text
    )

    # -> at line start: if it's just an image, emit bare (no blockquote wrapper)
    # otherwise → blockquote paragraph
    text = re.sub(r'^->\s+(!\[.*?\]\(.*?\)(?:\{[^}]*\})?)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^->\s+(.+)$', r'> \1', text, flags=re.MULTILINE)

    # Alpha + ordered lists — line-by-line pass to handle PMWiki's convention:
    # only the FIRST item in an alpha list has #%alpha%; subsequent items use plain #
    lines = text.split('\n')
    out_lines = []
    in_alpha = False
    alpha_buffer = []

    for line in lines:
        alpha_start = re.match(r'^#%alpha%\s*(.+)$', line)
        ordered_item = re.match(r'^(#+)\s+(.+)$', line)

        if alpha_start:
            in_alpha = True
            alpha_buffer.append(alpha_start.group(1))
        elif in_alpha and ordered_item and ordered_item.group(1) == '#':
            # Continue alpha list — plain # after #%alpha% stays alpha
            alpha_buffer.append(ordered_item.group(2))
        else:
            if alpha_buffer:
                out_lines.append(_flush_alpha(alpha_buffer))
                alpha_buffer = []
                in_alpha = False
            if ordered_item and not alpha_start:
                depth = len(ordered_item.group(1))
                content = ordered_item.group(2)
                indent = '    ' * (depth - 1)
                out_lines.append(f'{indent}1. {content}')
            else:
                out_lines.append(line)

    if alpha_buffer:
        out_lines.append(_flush_alpha(alpha_buffer))

    text = '\n'.join(out_lines)

    # Unordered list ** (nested) → indented - (space-after-marker form)
    text = re.sub(r'^\*\*\*\s+(.+)$', r'      - \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*\s+(.+)$', r'    - \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s+(.+)$', r'- \1', text, flags=re.MULTILINE)
    # No-space list items: *item and ##item (G2) — must fire after space forms
    text = re.sub(r'^\*\*\*(\S.*)$', r'      - \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\*(\S.*)$', r'    - \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\*(\S.*)$', r'- \1', text, flags=re.MULTILINE)
    text = re.sub(r'^##(\S.*)$', r'    1. \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#(\S.*)$', r'1. \1', text, flags=re.MULTILINE)

    # Headers — most-specific (longest marker) first; \s* handles no-space form
    # Negative lookahead (?!\[) prevents matching Markdown image syntax ![]
    text = re.sub(r'^!{4,}(?!\[)\s*(.+)$', r'#### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^!!!(?!\[)\s*(.+)$', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^!!(?!\[)\s*(.+)$', r'## \1', text, flags=re.MULTILINE)
    text = re.sub(r'^!(?!\[)\s*(.+)$', r'# \1', text, flags=re.MULTILINE)

    # Bold '''text''' and italic ''text''
    text = re.sub(r"'''(.+?)'''", r'**\1**', text)
    text = re.sub(r"''(.+?)''", r'*\1*', text)

    # [=...=] literal / escaped markup — unwrap
    text = re.sub(r'\[=(.*?)=\]', r'\1', text, flags=re.DOTALL)

    # PMWiki \\ forced line break → <br> (safe here because math is in placeholders)
    text = re.sub(r'\\\\\s*$', '<br>', text, flags=re.MULTILINE)

    # %% — closing PMWiki percent-style marker (must strip before general % rule)
    text = re.sub(r'%%', '', text)
    # Strip remaining % markup classes: %red%, %center%, %bgcolor=yellow%, etc. (G12)
    text = re.sub(r'%[a-zA-Z][a-zA-Z0-9_= -]*%', '', text)

    # Bare [[wiki sandbox]] or [[PmWiki/...]] internal links not in registry → plain text
    text = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('->')[-1].strip(), text)

    return text


# ---------------------------------------------------------------------------
# Full page conversion
# ---------------------------------------------------------------------------

def convert_page(page_name: str, text: str, link_registry: dict) -> str:
    """Convert decoded PMWiki text to QMD content string."""
    group = page_name.split('.')[0]

    # 1. Extract math
    text, math_store = extract_math(text)

    # 2. Strip server-side directives
    text = strip_directives(text)

    # 3. Code blocks
    text = convert_code_blocks(text)

    # 4. Block rules (order matters)
    text = convert_pipe_tables(text)
    text = convert_toggle_blocks(text)
    text = convert_note_blocks(text)
    text = convert_div_blocks(text)

    # 5. Inline rules
    text = convert_inline(text, group, link_registry)

    # 6. Restore math
    text = restore_math(text, math_store)

    # 7. Ensure blank line before any markdown table (CommonMark requirement)
    text = re.sub(r'(?<=\S)\n(\|)', r'\n\n\1', text)

    # 8. Clean up blank lines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def make_frontmatter(page_name: str, title: str = "") -> str:
    group, _, page = page_name.partition('.')
    if not title:
        if group == 'Class' and page.isdigit():
            title = f"Class {page}"
        elif group == 'Definition':
            title = f"Definition: {page}"
        elif group == 'Flex' and page.isdigit():
            title = f"Flex Day {page}"
        else:
            title = page.replace('-', ' ').title()

    return f"---\ntitle: \"{title}\"\n---\n\n"


# ---------------------------------------------------------------------------
# Schedule aggregation
# ---------------------------------------------------------------------------

def build_schedule_page(wiki_dir: Path) -> str:
    """Aggregate all Schedule.YYYYMMDD pages into a single schedule QMD."""
    schedule_files = sorted(
        [f for f in wiki_dir.iterdir() if f.name.startswith('Schedule.2')],
        key=lambda f: f.name
    )

    rows = []
    for sf in schedule_files:
        date_str = sf.name.split('.', 1)[1]
        # Strip trailing ,del-NNNNN suffixes
        date_str = date_str.split(',')[0]
        try:
            dt = datetime.strptime(date_str, '%Y%m%d')
            date_label = dt.strftime('%a %b %-d')
        except ValueError:
            continue

        page = decode_pmwiki_file(sf)
        note = page['text'].strip().replace('\n', ' ')[:200]
        note = re.sub(r'\(:.*?:\)', '', note).strip()
        if note:
            rows.append(f'| {date_label} | {note} |')

    header = "---\ntitle: \"Schedule\"\n---\n\n| Date | Notes |\n|------|-------|\n"
    return header + '\n'.join(rows) + '\n'


# ---------------------------------------------------------------------------
# Navigation builder
# ---------------------------------------------------------------------------

def build_quarto_yml(class_pages: list[str], def_pages: list[str], flex_pages: list[str]) -> str:
    """Generate _quarto.yml content."""

    def nav_item(page_name: str, link_registry: dict) -> str:
        path = link_registry.get(page_name, '')
        group, _, num = page_name.partition('.')
        if group == 'Class':
            label = f"Class {num}"
        elif group == 'Definition':
            label = num
        elif group == 'Flex':
            label = f"Flex {num}"
        else:
            label = num
        return f'        - text: "{label}"\n          href: {path}'

    link_registry = build_link_registry(class_pages + def_pages + flex_pages)

    class_items = '\n'.join(nav_item(p, link_registry) for p in class_pages)
    def_items = '\n'.join(nav_item(p, link_registry) for p in def_pages)
    flex_items = '\n'.join(nav_item(p, link_registry) for p in flex_pages) if flex_pages else ''

    flex_nav = ""
    if flex_items:
        flex_nav = f"""      - text: "Flex Days"
        menu:
{flex_items}
"""

    return f"""project:
  type: website
  output-dir: _site

website:
  title: "Math 119 — Applied Calculus for Data Analysis"
  favicon: assets/uploads/Class/119-bmw.png
  navbar:
    right:
      - text: "Home"
        href: index.qmd
      - text: "Definitions"
        menu:
{def_items}
      - text: "Schedule"
        href: schedule.qmd
  page-footer:
    center: "Math 119 — BYU-Idaho"

format:
  html:
    theme: flatly
    css: styles.css
    toc: true
    toc-depth: 3
    html-math-method:
      method: mathjax
      url: "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"
    include-in-header:
      text: |
        <script>
        window.MathJax = {{
          tex: {{
            macros: {{
              ds: "\\\\displaystyle"
            }}
          }}
        }};
        </script>

execute:
  freeze: auto
"""


def build_styles_css() -> str:
    return """\
/* Math 119 Quarto Site Styles */

details {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  margin: 1rem 0;
  background: #f8f9fa;
}

details summary {
  cursor: pointer;
  font-weight: 600;
  color: #495057;
  padding: 0.25rem 0;
}

details[open] summary {
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #dee2e6;
}

.indent {
  margin-left: 2em;
}

ol[type="a"] {
  list-style-type: lower-alpha;
}

/* Prevent wide tables from breaking layout — scroll horizontally */
table {
  display: block;
  overflow-x: auto;
  max-width: 100%;
}

table td, table th {
  white-space: normal;
  word-wrap: break-word;
  min-width: 120px;
}

table td:first-child, table th:first-child {
  min-width: 3rem;
  white-space: nowrap;
}

/* Left-align display math (MathJax centered by default looks odd in lists) */
mjx-container[display="true"] {
  text-align: left !important;
  margin-left: 0 !important;
}

/* Schedule table borders */
.schedule-table {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  min-width: 600px;
  display: table;
}

.schedule-table th,
.schedule-table td {
  border: 1px solid #dee2e6;
  padding: 0.4rem 0.6rem;
  vertical-align: top;
  min-width: unset;
  white-space: normal;
}

.schedule-table thead {
  background: #e9ecef;
  font-weight: 600;
}
"""


def build_index_qmd() -> str:
    return """\
---
title: "Math 119 — Applied Calculus for Data Analysis"
---

Welcome to the Math 119 course wiki for BYU-Idaho.

Use the navigation above to browse **Class Sessions**, **Definitions**, and the **Schedule**.

This site is generated from the course PMWiki at [byuimath.com/bmw/all/119/](https://byuimath.com/bmw/all/119/){target="_blank"}.
"""


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def get_class_pages(wiki_dir: Path) -> list[str]:
    pages = [
        f.name for f in wiki_dir.iterdir()
        if f.name.startswith('Class.') and f.name.split('.')[1].isdigit()
    ]
    return sorted(pages, key=lambda p: int(p.split('.')[1]))


def get_group_pages(wiki_dir: Path, group: str) -> list[str]:
    pages = [
        f.name for f in wiki_dir.iterdir()
        if f.name.startswith(f'{group}.')
        and not f.name.endswith('RecentChanges')
        and f.name.split('.')[1] not in ('', 'RecentChanges', 'List')
    ]
    if group == 'Flex':
        return sorted(
            [p for p in pages if p.split('.')[1].isdigit()],
            key=lambda p: int(p.split('.')[1])
        )
    return sorted(pages)


def run_conversion(page_filter: str = None, dry_run: bool = False):
    if not WIKI_DIR.exists() or not any(WIKI_DIR.iterdir()):
        raise SystemExit("ERROR: pmwiki_data/wiki.d/ is empty. Run: uv run pull_wiki.py first.")

    class_pages = get_class_pages(WIKI_DIR)
    def_pages = get_group_pages(WIKI_DIR, 'Definition')
    flex_pages = get_group_pages(WIKI_DIR, 'Flex')

    all_pages = class_pages + def_pages + flex_pages
    link_registry = build_link_registry(all_pages)

    if page_filter:
        all_pages = [p for p in all_pages if p == page_filter]
        if not all_pages:
            raise SystemExit(f"ERROR: Page '{page_filter}' not found or not in a convertible group.")

    print(f"Converting {len(all_pages)} pages... (dry_run={dry_run})")

    # Scaffold site structure
    if not dry_run:
        for folder in ['class', 'definitions', 'flex', 'assets/uploads']:
            (SITE_DIR / folder).mkdir(parents=True, exist_ok=True)

        if not page_filter:
            # Static files — skip on single-page runs
            (SITE_DIR / '_quarto.yml').write_text(
                build_quarto_yml(class_pages, def_pages, flex_pages)
            )
            (SITE_DIR / 'styles.css').write_text(build_styles_css())

            index_path = SITE_DIR / 'index.qmd'
            if not index_path.exists():
                index_path.write_text(build_index_qmd())

            # Schedule — generate_schedule.py owns this file after first run
            schedule_content = build_schedule_page(WIKI_DIR)
            (SITE_DIR / 'schedule.qmd').write_text(schedule_content)
            print("  wrote: site/schedule.qmd")

            # Copy uploads
            if UPLOADS_DIR.exists():
                dest_uploads = SITE_DIR / 'assets' / 'uploads'
                for src_file in UPLOADS_DIR.rglob('*'):
                    if src_file.is_file():
                        rel = src_file.relative_to(UPLOADS_DIR)
                        dest = dest_uploads / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        if not dest.exists() or dest.stat().st_size != src_file.stat().st_size:
                            shutil.copy2(src_file, dest)
                            print(f"  copied: assets/uploads/{rel}")

    # Convert pages
    for page_name in all_pages:
        file_path = WIKI_DIR / page_name
        page_data = decode_pmwiki_file(file_path)
        qmd_body = convert_page(page_name, page_data['text'], link_registry)
        frontmatter = make_frontmatter(page_name)
        qmd_content = frontmatter + qmd_body + '\n'

        group, _, page = page_name.partition('.')
        if group == 'Class':
            out_path = SITE_DIR / 'class' / f'class-{page}.qmd'
        elif group == 'Definition':
            out_path = SITE_DIR / 'definitions' / f'{page.lower()}.qmd'
        elif group == 'Flex':
            out_path = SITE_DIR / 'flex' / f'flex-{page}.qmd'
        else:
            continue

        if dry_run:
            print(f"  [dry-run] would write: {out_path.relative_to(REPO_ROOT)}")
            print(qmd_content[:300])
            print("  ...")
        else:
            out_path.write_text(qmd_content)
            print(f"  wrote: {out_path.relative_to(REPO_ROOT)}")

    # GitHub Actions workflow
    workflow_dir = REPO_ROOT / '.github' / 'workflows'
    workflow_path = workflow_dir / 'publish.yml'
    if not dry_run and not workflow_path.exists():
        workflow_dir.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(GITHUB_ACTIONS_WORKFLOW)
        print("  wrote: .github/workflows/publish.yml")

    print(f"\nDone. {'(dry run — nothing written)' if dry_run else 'Run: cd site && quarto preview'}")


GITHUB_ACTIONS_WORKFLOW = """\
name: Publish Quarto Site

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Quarto
        uses: quarto-dev/quarto-actions/setup@v2

      - name: Publish to GitHub Pages
        uses: quarto-dev/quarto-actions/publish@v2
        with:
          target: gh-pages
          path: site
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert PMWiki to Quarto site')
    parser.add_argument('--page', help='Convert a single page (e.g. Class.5)')
    parser.add_argument('--dry-run', action='store_true', help='Show output without writing files')
    args = parser.parse_args()

    run_conversion(page_filter=args.page, dry_run=args.dry_run)
