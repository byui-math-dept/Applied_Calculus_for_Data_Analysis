# PMWiki → Quarto Quality Check Agent Guide

## Agent Instructions
1. Read this for mission, gotcha checklist, principles, and pitfalls.
2. Parse `pmwiki_quality_check.json` for all check rules, patterns, severity weights, and validation test cases.
3. Implementation script: `tools/quality_check.py` — run it to scan `site/` against `pmwiki_data/wiki.d/`.
4. Always run this agent AFTER `pmwiki_to_quarto.py` and BEFORE pushing to the quarto-site remote.

---

## Mission

**What it does**: Scans every converted QMD file in `site/` for leaked PMWiki markup, missed conversion patterns, and structural issues — then cross-references against the original wiki flat files to catch anything the converter silently skipped.

**Why it exists**: The PMWiki → Quarto converter handles the common cases, but PMWiki has a wide surface area of markup. Real course pages use pipe tables, inline monospace, definition lists, superscripts, and other patterns the converter may not cover. A silent miss produces broken output that students see without any error being thrown. This agent catches those misses before they go live.

**Who uses it**: Chaz Clark (Math 119 instructor), run as part of the site rebuild workflow, or as a standalone check after any converter update.

**Example**: "Quality check found 3 pages with leaked `||` pipe table syntax, 7 pages with unconverted `*item` list items (no space after `*`), and 2 pages where `#item` ordered list items without spaces were dropped. Generated a report with exact file/line references and suggested converter fixes."

---

## Agent Quickstart

1. **Scan QMD files**: For each `.qmd` in `site/class/`, `site/definitions/`, `site/flex/` — run all leak-detection patterns from `pmwiki_quality_check.json → checks.leak_patterns`.
2. **Cross-reference originals**: For each flagged page, decode the original wiki flat file and identify the source markup that was missed.
3. **Categorize**: Assign severity (critical/high/medium/low) per check rule.
4. **Report**: Write `quality_report.md` at repo root with findings grouped by severity, each with file, line number, original wiki text, and current QMD output.
5. **Optionally re-convert**: For critical/high issues on specific pages, call `uv run python tools/pmwiki_to_quarto.py --page PageName` to regenerate.

For check patterns, severity weights, and test cases, see `pmwiki_quality_check.json`.

---

## File Organization: JSON vs MD

### This Markdown File Contains
- Mission and why quality checking matters
- The full "gotcha" list with explanations (the WHY behind each check)
- Principles guiding check design
- Common false positives and how to distinguish them
- External system lessons from the PMWiki markup reference

### The JSON File Contains
- All leak-detection regex patterns with severity ratings
- Cross-reference rules (what to look for in the original wiki file)
- Report format specification
- Validation test cases (known-bad inputs with expected detections)

---

## Key Principles

### 1. Leak Detection Over Correctness Checking
**Description**: Check for raw PMWiki markup that leaked into QMD output, not for whether the converted content is "correct." Correctness requires understanding course intent; leak detection is mechanical and reliable.

**Why**: A page with `>>toggle<<` literally in the QMD is unambiguously wrong. A page where a toggle was converted to `<details>` but the inner content has a formatting quirk may be acceptable. Focus on what can be checked programmatically.

**How**: All checks in `pmwiki_quality_check.json → checks.leak_patterns` are patterns that should never appear in valid QMD output. Any match is a confirmed issue.

### 2. Cross-Reference to Understand, Not to Re-Convert
**Description**: When a leak is found, decode the original wiki page to understand the source markup — but don't automatically re-convert. Re-converting may overwrite manual edits to the QMD.

**Why**: Some QMD files may have been manually edited after conversion (e.g., board photos added, notes inserted). A blind re-convert would wipe those changes.

**How**: Report the original wiki markup alongside the leaked output. Let the instructor decide: re-convert the page or hand-fix the QMD.

### 3. Severity Tiers Drive Action
**Description**: Critical and high issues block the site push. Medium issues are reported but don't block. Low issues are informational only.

**Why**: Not every conversion imperfection prevents a usable page. A missing superscript is less urgent than a leaked table that renders as literal `||` characters.

**How**: See `pmwiki_quality_check.json → checks.severity_policy` for tier definitions and blocking thresholds.

### 4. False Positive Awareness
**Description**: Some patterns that look like leaked PMWiki markup are legitimate in QMD output. The check rules are tuned to avoid these.

**Why**: `$...$` in QMD is valid LaTeX, not a conversion miss. `>` at line start is a Markdown blockquote. `---` is a horizontal rule. `[[` inside a code fence is literal text. Flagging these as issues wastes time and erodes trust in the quality check.

**How**: All leak patterns are scoped to avoid false positives — see the `notes` field on each pattern in the JSON for the specific exclusion logic.

---

## The Gotcha List

These are patterns found in the Math 119 PMWiki that the converter can miss. Each one is a check rule in the JSON.

### G1 — Pipe Table Syntax (`||...||`) — CRITICAL
PMWiki's most common table format uses double-pipe delimiters, not `(:table:)` directives. These tables appear in Flex pages (logarithm matching exercises) and are entirely invisible as structured content if they leak through.

**Source pattern**: Lines starting with `||`, cells separated by `||`, headers marked `||!`.
**Leaked output looks like**: `||!Expanded Expressions ||!Condensed Expressions ||`
**Should be**: A Markdown/HTML table.
**Check**: Any line matching `^\|\|` in a QMD file.

### G2 — List Items Without Space (`*item`, `#item`) — CRITICAL
PMWiki allows list markers without a space before the content (`*item`, `#text`). The converter's regexes require `\s+` after the marker, so these pass through unconverted.

**Source pattern**: `*Take turns acting as scribe` (no space after `*`)
**Leaked output looks like**: `*Take turns acting as scribe` (literal asterisk, not a list)
**Should be**: `- Take turns acting as scribe`
**Check**: Lines matching `^\*\S` or `^#+[^%\s]` in a QMD file (outside code fences).

### G3 — Unconverted Headers Inside Blocks — HIGH
Headers (`!!`, `!!!`) that appear inside toggle or note blocks that were processed before inline rules ran can survive as raw `!!` text if the block processing extracted them before the header rule fired.

**Source pattern**: `!!Group Discussion` inside a `>>toggle<<` block
**Leaked output**: `!!Group Discussion` as literal text in a `<details>` block
**Should be**: `## Group Discussion`
**Check**: Lines matching `^!!+\s` in a QMD file.

### G4 — Monospace / Inline Code (`@@text@@`) — HIGH
PMWiki's `@@text@@` inline code markup is not handled by the converter. This appears in class pages that reference variable names, function syntax, or keyboard keys.

**Source pattern**: `@@draw_pmf@@`
**Leaked output**: `@@draw_pmf@@`
**Should be**: `` `draw_pmf` ``
**Check**: Any `@@` in a QMD file outside a code fence.

### G5 — Superscript (`^text^`) — MEDIUM
PMWiki superscript syntax `^text^` passes through unconverted. Quarto supports `^text^` natively — so the output is actually correct — but the surrounding space handling may differ. Check for adjacent math conflicts.

**Source pattern**: `10^3^` (superscript 3)
**Note**: This is actually valid in Quarto (`^text^` = superscript). Only flag if adjacent to math or if the `^` is inside a `$...$` block where it's part of LaTeX syntax. The common false positive is `cm'^2^'` where the `'` marks are remnants of italic markup — Quarto renders this correctly as `cm`².

### G6 — Strikethrough (`{-text-}`) — MEDIUM
PMWiki strikethrough `{-text-}` is not converted. It appears occasionally in revised problem statements.

**Source pattern**: `{-old answer-}`
**Leaked output**: `{-old answer-}`
**Should be**: `~~old answer~~`
**Check**: `\{-.*?-\}` in a QMD file.

### G7 — Definition Lists (`:term:definition`) — MEDIUM
PMWiki definition list syntax `:term:definition` at line start. Appears in the Definition group pages.

**Source pattern**: `:logarithm:The exponent to which a base must be raised`
**Leaked output**: `:logarithm:The exponent to which a base must be raised` (renders oddly)
**Should be**: `**logarithm**\n: The exponent to which a base must be raised`
**Check**: Lines matching `^:[^:]+:[^:]` in a QMD file.

### G8 — Horizontal Rules (`----`) — LOW
PMWiki `----` (4+ dashes) horizontal rules. Markdown uses `---` (3 dashes). Four dashes are also valid Markdown, so this usually renders correctly — flag as informational only.

**Check**: Lines matching `^----+$` — technically valid Markdown but confirm intent.

### G9 — Force Line Break (`\\`) — LOW
PMWiki `\\` at line end forces a line break. In QMD this renders as literal `\\`. Should be two trailing spaces or `<br>`.

**Source pattern**: `See the board\\ for the sketch`
**Check**: `\\\\\s*$` at line end in a QMD file.

### G10 — Text Size Markup (`[+text+]`, `[-text-]`) — LOW
PMWiki text sizing `[+large+]`, `[++larger++]`, `[-small-]`. These pass through as literal brackets. Low priority since they're cosmetic.

**Check**: `\[[\+\-]{1,2}[^\]]+[\+\-]{1,2}\]` in a QMD file.

### G11 — Pipe-Style Links (`[[text | url]]`) — HIGH
Alternative PMWiki link syntax using `|` as separator instead of `->`. The converter only handles `->` form. If a page uses `[[display | http://url]]`, the link leaks through unconverted.

**Source pattern**: `[[Syllabus | https://byui.instructure.com/courses/398938]]`
**Check**: `\[\[[^\]]+\|[^\]]+\]\]` in a QMD file.

### G12 — Remaining `%...%` Style Markup — MEDIUM
After the converter strips known `%` markup classes, some compound forms may survive: `%bgcolor=yellow%`, `%item value=3%`, `%define=...%`. The strip rule uses `%[a-zA-Z][a-zA-Z0-9_-]*%` which misses compound forms with `=`.

**Check**: `%[a-zA-Z][a-zA-Z0-9_=]+%` in a QMD file.

### G13 — PMWiki Directives Leaking (`(:...:)`) — CRITICAL
Any `(:...:)` directive surviving in output means a server-side command was not stripped. Students would see raw directive text.

**Check**: `\(:[a-zA-Z]` in a QMD file.

### G14 — Raw `Attach:` References — CRITICAL
`Attach:filename` that was not matched by the image conversion rule (e.g., unusual file extensions, or Attach: in a context the regex didn't reach).

**Check**: `\bAttach:[A-Za-z]` in a QMD file.

### G15 — URL-Encoded Sequences Surviving (`%25`, `%0a`) — HIGH
If URL decoding failed or was partial, encoded sequences appear literally in output.

**Check**: `%25|%0a|%3c|%3e` in a QMD file.

### G16 — Raw `>>...<<` Div Tags — CRITICAL
Any surviving `>>word<<` or `>><<` means a div block was not processed — most likely a nested or malformed toggle/indent block.

**Check**: `>>[a-z]+<<|>><<` in a QMD file.

### G17 — Unclosed `<details>` Tags — HIGH
If a toggle block was partially converted, the output may contain an opening `<details>` without a matching `</details>`, which breaks page rendering.

**Check**: Count `<details>` vs `</details>` occurrences per file — they must match.

---

### G18 — Bare `#anchorname` at Line Start — CRITICAL
PMWiki `[[#PP]]` anchor definitions get stripped to `#PP` by a naive bare-link handler, then appear to be no-space ordered list items. This is a converter pipeline ordering bug — anchor rules must fire before bare link rules.

**Source pattern**: `[[#PP]]` or `[[#Prep]]`
**Leaked output**: `#PP` (looks like a no-space list item, also corrupts G2 detection)
**Should be**: `<a id="PP"></a>`
**Check**: Covered by G2 (`^#+[^#%\s]`) — any `#word` at line start is suspect. Cross-reference against wiki source to confirm it was `[[#...]]`.

### G19 — `(:comment:)` Directive — CRITICAL
`(:comment text:)` is a server-side PMWiki comment — invisible on the live wiki, visible as raw text in QMD output. These blocks can span multiple lines and may contain `%%` delimiters inside.

**Source pattern**: `(:comment %%%%Work that can be completed after class%%%%:)`
**Leaked output**: `(:comment %%%% ...` appearing as literal text
**Should be**: (stripped entirely)
**Check**: Covered by G13 (`\(:[a-zA-Z]`).

### G20 — `(:include:)` Page Transclusion — CRITICAL  
`(:include Page.Name:)` is server-side page include. With no PHP server, students see the raw directive text.

**Source pattern**: `(:include Definition.Logarithm:)`
**Leaked output**: `(:include Definition.Logarithm:)` literal text on the page
**Should be**: The converter replaces with `<!-- include: Definition.Logarithm -->` (HTML comment for traceability)
**Check**: Covered by G13.

---

## How to Use This Agent

### Prerequisites
- `site/` directory populated (run `uv run python tools/pmwiki_to_quarto.py` first)
- `pmwiki_data/wiki.d/` present (for cross-referencing originals)
- `uv sync` run (Python env with pyyaml)

### Existing Tooling

| Tool / File | Purpose | When to use |
|---|---|---|
| `tools/pmwiki_to_quarto.py` | Converter | Run before quality check to generate/update site/ |
| `tools/quality_check.py` | Quality scanner | Run after every conversion to catch issues |
| `pmwiki_data/wiki.d/` | Original wiki files | Cross-reference source when a leak is found |

### Basic Usage

```bash
# Full quality scan — all converted pages
uv run python tools/quality_check.py

# Scan a single page
uv run python tools/quality_check.py --page Class.14

# Scan and fail (exit code 1) if any critical/high issues found — for CI
uv run python tools/quality_check.py --strict
```

Output: `quality_report.md` at repo root.

---

## Common Pitfalls and Solutions

### 1. Flagging LaTeX as Leaked Markup
**Problem**: `$f(x) = x^2$` triggers the `^text^` superscript check (G5) because `^` appears inside math.
**Solution**: All checks are applied only outside math regions — the quality scanner extracts math placeholders before running checks, same as the converter. Never flag content inside `$...$` or `$$...$$`.

### 2. Flagging Content Inside Code Fences
**Problem**: R code inside ` ```r ``` ` blocks contains `#`, `*`, `<-` and other characters that look like leaked markup.
**Solution**: Skip all content inside fenced code blocks (` ```...``` ` and `[@...@]`). The scanner extracts code blocks before running checks.

### 3. False Positives on Markdown Blockquotes
**Problem**: `> text` is valid Markdown, not a leaked PMWiki `>>comment<<` fragment.
**Solution**: G16 checks for `>>[a-z]+<<` and `>><<` specifically (double angle brackets with content or empty), not single `>`.

### 4. Re-Converting Overwrites Manual Edits
**Problem**: Running `pmwiki_to_quarto.py --page Class.14` after adding board photos to `site/class/class-14.qmd` wipes the photos.
**Solution**: Before re-converting a page, check `git diff site/class/class-14.qmd` for manual additions. If present, hand-fix the leaked markup instead of re-converting.

---

## External System Lessons

### PMWiki Pipe Tables — Header Cells Use `||!` Not `||#`
**Behavior**: PMWiki header cells use `||!text||` (exclamation mark), not `||#text||` or `||**text**||`. The `!` must immediately follow `||` with no space.

**Why it matters**: A detection pattern like `\|\|[A-Z]` would miss `||!Header` (since `!` is not uppercase). The correct detection pattern is `^\|\|` (any line starting with `||`).

### PMWiki Lists — `#` and `*` Don't Require Space Before Content
**Behavior**: Unlike Markdown where `#text` is a heading and `* text` requires the space, PMWiki treats `*text` and `#text` at line start as list items regardless of spacing.

**Why it matters**: The converter's original regexes used `\s+` (requiring space), silently dropping no-space list items. The quality check catches these specifically because they're a known converter blind spot.

### PMWiki Alpha Lists — Only First Item Tagged
**Behavior**: In a lettered list `a) b) c)`, PMWiki only places `#%alpha%` on the first item. Subsequent items use plain `#`. This is a PMWiki convention, not documented in the official markup reference.

**Why it matters**: A quality check that looks for `#%alpha%` will only find the first item of each alpha list. The real check is to look for `#` items immediately following an alpha list in the original wiki — those are the ones that need the stateful alpha list handler.

---

## Validation and Testing

### Quick Validation
```bash
# Inject a known-bad pattern and confirm detection
echo "||!Header||" >> site/class/class-1.qmd
uv run python tools/quality_check.py --page Class.1
# Should report: G1 (pipe table) — CRITICAL
git checkout site/class/class-1.qmd  # restore
```

### Quality Bar
- [ ] All 17 gotcha checks run against every converted page
- [ ] No false positives on math content or code fences
- [ ] `quality_report.md` groups findings by severity
- [ ] Exit code 0 when no critical/high issues; exit code 1 when any found with `--strict`
- [ ] Cross-reference shows original wiki line for each finding
- [ ] Runs in under 10 seconds for all 68 pages

---

## Resources and References

### Agent Files
- **`pmwiki_quality_check.json`**: Check patterns, severity rules, test cases
- **`tools/quality_check.py`**: Scanner implementation
- **`tools/pmwiki_to_quarto.py`**: The converter this agent validates

### Related Agents
- `pmwiki_quarto` — the converter agent; fix converter rules when this agent finds systematic misses

### External Documentation
- [PmWiki TextFormattingRules](https://www.pmwiki.org/wiki/PmWiki/TextFormattingRules) — authoritative markup reference
- [PmWiki Tables](https://www.pmwiki.org/wiki/PmWiki/Tables) — pipe table syntax spec
- [PmWiki MarkupMasterIndex](https://www.pmwiki.org/wiki/PmWiki/MarkupMasterIndex) — complete pattern index
- [pmdown converter](https://github.com/dohliam/pmdown) — reference implementation for edge cases

---

## Quick Reference Card

| Aspect | Value |
|--------|-------|
| **Purpose** | Detect leaked PMWiki markup in converted Quarto QMD files |
| **Input** | `site/` QMD files + `pmwiki_data/wiki.d/` originals |
| **Output** | `quality_report.md` with severity-grouped findings |
| **Agent Type** | `rule_based` |
| **Complexity** | standard |
| **Key Files** | `pmwiki_quality_check.json`, `tools/quality_check.py` |
| **Quickstart** | `uv run python tools/quality_check.py` |
| **Common Pitfall** | Flagging LaTeX `^` as superscript markup — always skip math regions first |
| **Dependencies** | `site/` populated, `pmwiki_data/wiki.d/` present, Python 3.14 |
