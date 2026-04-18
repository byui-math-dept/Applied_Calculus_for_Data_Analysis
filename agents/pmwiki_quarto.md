# PMWiki → Quarto Agent Guide

## Agent Instructions
1. Read this for mission, principles, quickstart, and pitfalls.
2. Parse `pmwiki_quarto.json` for structured data: markup rules, conversion tables, tool definitions, and validation cases.
3. The implementation script is `tools/pmwiki_to_quarto.py` — it handles file I/O, URL-decoding, markup conversion, and Quarto project scaffolding.
4. Always run a fresh `uv run pull_wiki.py` before converting to ensure `pmwiki_data/` is current.

---

## Mission

**What it does**: Converts a locally-synced PMWiki installation (`pmwiki_data/`) into a fully-functional Quarto website deployed to GitHub Pages via GitHub Actions. Handles the complete pipeline: URL-decoding PMWiki flat files, translating PmWiki markup to QMD, scaffolding the Quarto project, generating navigation, copying uploads, and wiring the GitHub Actions publish workflow.

**Why it exists**: The Math 119 course wiki at `byuimath.com/bmw/all/119/` uses PmWiki as its delivery platform. The goal is to migrate to a modern, version-controlled, GitHub Pages–hosted site that preserves all content features (LaTeX math, collapsible answers, structured class sessions) without requiring a PHP server.

**Who uses it**: Chaz Clark, Math 119 instructor at BYU-Idaho, building and maintaining the course Quarto site from the PMWiki source files.

**Example**: "Agent decoded Class.1 through Class.36, converted PmWiki markup (headers, ordered lists, LaTeX, toggle blocks, attach images) to QMD, scaffolded `_quarto.yml` with a sidebar listing all 36 class sessions, copied uploads into `site/assets/`, and generated the GitHub Actions publish workflow. Running `quarto preview` showed the rendered site with working MathJax and collapsible answer blocks."

---

## Agent Quickstart

1. **Sync**: Confirm `pmwiki_data/` is current — run `uv run pull_wiki.py` if needed.
2. **Parse pages**: Call `decode_pmwiki_file()` for each file in `pmwiki_data/wiki.d/` to extract URL-decoded page text and metadata (name, mtime, rev).
3. **Convert**: Call `convert_pmwiki_to_qmd()` on each decoded page — applies all markup translation rules from `pmwiki_quarto.json → markup_rules`.
4. **Scaffold**: Call `setup_quarto_project()` to write `_quarto.yml`, `index.qmd`, and folder structure into `site/`.
5. **Nav**: Call `build_navigation()` to generate the sidebar from the Class.* page list, sorted numerically.
6. **Assets**: Call `copy_uploads()` to mirror `pmwiki_data/uploads/` → `site/assets/uploads/`.
7. **CI**: Write `.github/workflows/publish.yml` using `quarto-dev/quarto-actions/publish@v2` targeting `gh-pages`.
8. **Validate**: Run `quarto check` and `quarto preview` — verify math renders, toggles work, navigation is correct.

For markup translation rules, tool parameters, and validation test cases, see `pmwiki_quarto.json`.

---

## File Organization: JSON vs MD

### This Markdown File Contains
- Mission and why this agent exists
- Conversion workflow narrative
- Pitfalls with explanations and context
- PmWiki-specific course knowledge (what the markup idioms mean)
- GitHub Pages / Quarto design decisions

### The JSON File Contains
- Full markup translation rule table (PmWiki → QMD regex patterns)
- Tool definitions with parameters and input examples
- `_quarto.yml` template structure
- GitHub Actions workflow template
- Validation test cases with before/after pairs
- Site structure specification

---

## Key Principles

### 1. Decode Before Converting
**Description**: Every PMWiki flat file stores its `text=` field as URL-encoded content. Decoding must happen first — converting raw encoded text produces garbage.

**Why**: PmWiki uses `%0a` for newlines, `%3c`/`%3e` for `<`/`>`, `%25` for `%`, and so on throughout. A regex that matches `!!` headers will fail if the file still contains `%0a!!`.

**How**: Extract the `text=` line from each file, split on the first `=`, then `urllib.parse.unquote()` the value. Process the resulting plain text through the markup rules.

### 2. Order Markup Rules by Specificity
**Description**: Apply more-specific rules before less-specific ones to avoid partial matches that corrupt output.

**Why**: The `%25newwin%25[[text -> url]]` pattern overlaps with the plain `[[text -> url]]` pattern. If the plain link rule runs first, it leaves `%25newwin%25` as a dangling prefix in the QMD. Similarly, `#%25alpha%25` list items must be matched before plain `#` list items.

**How**: Rules in `pmwiki_quarto.json → markup_rules` are ordered — apply them in the listed sequence without reordering.

### 3. Math Passes Through Untouched
**Description**: PMWiki LaTeX (`$...$`, `$$...$$`, `\begin{cases}...\end{cases}`) is already valid MathJax/KaTeX and must not be processed by any other rule.

**Why**: Markup rules that operate on `*`, `#`, or `[[` patterns can fire inside math expressions and corrupt them. A rule matching `*` for bullet lists will damage `a^* + b^*` inside a math block.

**How**: Before applying any markup rules, extract all math regions and replace them with non-colliding placeholders (e.g., `MATHBLOCK_0`, `MATHINLINE_1`). Restore them after all other rules have run.

### 4. Toggle Blocks Become `<details>`
**Description**: PMWiki's `>>toggle<<...>><<` pattern (used for collapsible answer sections) maps to HTML `<details><summary>Answers</summary>...</details>`, not Quarto callouts.

**Why**: Quarto callout blocks (`::: {.callout-note}`) are always visible. The Math 119 course relies heavily on student self-assessment: students try problems, then reveal answers. `<details>` is the correct semantic element and renders in any Quarto output format including HTML.

**How**: Match `>>toggle<<\n(.*?)\n>><<` (multiline, non-greedy) and wrap in `<details><summary>Answers</summary>` ... `</details>`. Content between the tags is already converted QMD/HTML.

### 5. Preserve Internal Link Structure
**Description**: PMWiki internal links (`[[Class.5]]`, `[[Class.5 -> Class.5]]`) must resolve to the correct relative `.qmd` path in the output site.

**Why**: The site uses a `class/` subdirectory structure (`class/class-5.qmd`). A link rendered as `[Class.5](Class.5)` will 404 at runtime.

**How**: Maintain a page-name-to-output-path registry. When converting links, look up the target in the registry and emit the correct relative path. See `pmwiki_quarto.json → link_registry_rules`.

### 6. GitHub Actions Workflow Is Non-Negotiable
**Description**: The publish workflow must use `quarto-dev/quarto-actions/publish@v2` with `target: gh-pages` and a `GITHUB_TOKEN` secret. Do not use `peaceiris/actions-gh-pages` or manual `git push`.

**Why**: `quarto-dev/quarto-actions` handles Quarto installation, caching, and branch management correctly. Manual push workflows break when Quarto changes its output directory structure.

**How**: Write `.github/workflows/publish.yml` from the template in `pmwiki_quarto.json → github_actions_template`. Do not modify the workflow structure without testing locally with `quarto publish gh-pages` first.

---

## Domain Terms

| Term | Definition |
|------|------------|
| `pmwiki_data/wiki.d/` | Local directory of PMWiki flat files, one per page. File names use `Group.PageName` format (e.g., `Class.1`, `Definition.Logarithm`). |
| `text=` field | The URL-encoded page content field in each PMWiki flat file. This is the only field that gets converted — all other fields (metadata, diffs) are ignored. |
| PmWiki markup | The custom wiki markup language used by PMWiki — distinct from MediaWiki/Markdown. Documented in `pmwiki_quarto.json → markup_rules`. |
| `>>toggle<<...>><<` | PMWiki div markup for collapsible sections. The course uses these exclusively for student answer reveals. Maps to `<details>`. |
| `(:note:)...(:noteend:)` | PMWiki custom markup for instructor notes/asides. Maps to Quarto `::: {.callout-note}` blocks. |
| `(:if false:)...(:if:)` | PMWiki conditional block where `false` means the content is hidden in the live wiki. These sections are skipped during conversion. |
| `Attach:filename.png` | PMWiki image attachment reference. Maps to `![](../assets/uploads/GroupName/filename.png)` with the correct group path. |
| `%25newwin%25` | PMWiki markup prefix meaning "open in new window." Translates to `{target="_blank"}` on Quarto links. |
| `site/` | Output directory for the Quarto project. Gitignored except for `_quarto.yml`, `*.qmd` source files, and `.github/`. |
| `gh-pages` | The GitHub Pages branch that Quarto publishes rendered HTML to. Never edit this branch directly. |

---

## How to Use This Agent

### Prerequisites
- `pmwiki_data/` synced (run `uv run pull_wiki.py`)
- `uv` installed, `uv sync` run (Python 3.14, all deps)
- Quarto CLI installed (`quarto check` passes)
- GitHub repo with Pages enabled (Settings → Pages → Source: Deploy from branch `gh-pages`)
- `GITHUB_TOKEN` available in Actions (automatic for public repos)

### Existing Tooling

| Tool / File | Purpose | When to use |
|---|---|---|
| `pull_wiki.py` | SFTP sync from server → `pmwiki_data/` | Before any conversion run to get latest content |
| `tools/pmwiki_to_quarto.py` | Full conversion pipeline | Main conversion script — run this to regenerate `site/` |
| `pmwiki_data/wiki.d/` | Source PMWiki flat files | Read-only input; never edit these |
| `pmwiki_data/uploads/` | Course images and attachments | Copied to `site/assets/uploads/` by the converter |
| `site/_quarto.yml` | Quarto project config | Edit to adjust nav, theme, or site metadata |

### Basic Usage

**Step 1: Sync latest wiki content**
```bash
uv run pull_wiki.py
```

**Step 2: Run the converter**
```bash
uv run python tools/pmwiki_to_quarto.py
# Output: site/ directory with all QMD files + _quarto.yml
```

**Step 3: Preview locally**
```bash
cd site && quarto preview
```

**Step 4: Push to GitHub Pages**
```bash
# First time only — set up gh-pages branch
cd site && quarto publish gh-pages

# After initial setup, GitHub Actions publishes on every push to main
git push origin main
```

### Advanced Usage

**Rebuild a single page** (faster than full conversion):
```bash
uv run python tools/pmwiki_to_quarto.py --page Class.14
```

**Dry-run** (show what would change without writing):
```bash
uv run python tools/pmwiki_to_quarto.py --dry-run
```

**Add class notes or board images**: Drop files into `site/assets/notes/` and reference them from the relevant `class/class-N.qmd` file manually, or add a notes section to the converter's page template.

---

## Common Pitfalls and Solutions

### 1. Math Expressions Corrupted by List Rules

**Problem**: Ordered-list rule (`^#\s` → `1. `) fires inside a displayed math block and corrupts equations like `\begin{cases} # item`.

**Why it happens**: PmWiki uses `#` for both ordered lists (at line start) and inside LaTeX case environments. A line-start anchor (`^`) regex is usually sufficient, but multiline math blocks can have `#` on its own line at column 0.

**Solution**: Always extract and placeholder-replace math regions before applying any markup rules. See `pmwiki_quarto.json → conversion_pipeline.step_order`.

### 2. Toggle Content Not Rendering After Conversion

**Problem**: Answer blocks appear as raw `<details>` tags in the Quarto output instead of rendering as collapsible HTML.

**Why it happens**: Quarto's Markdown processor may not render raw HTML inside fenced divs if `format: html` is not set in `_quarto.yml`, or if the `<details>` tag contains un-converted PmWiki markup (because the toggle content was extracted before inner rules ran).

**Solution**: Apply inner markup rules to toggle content before wrapping in `<details>`. Ensure `_quarto.yml` has `format: html: html-math-method: mathjax` set. Quarto passes raw HTML blocks through by default in HTML output.

### 3. Numbered Class Pages Sort as Strings

**Problem**: Sidebar navigation shows Class sessions in string order: 1, 10, 11, 12, ..., 2, 20, 21, ...

**Why it happens**: `os.listdir()` and glob return filenames as strings. `Class.10` sorts before `Class.2`.

**Solution**: Sort Class.* pages by extracting the integer suffix: `sorted(pages, key=lambda p: int(p.split('.')[-1]))`. This is enforced in `build_navigation()`.

### 4. Attach: Images Pointing to Wrong Group Path

**Problem**: `Attach:119-bmw.png` in `Class.1` renders as a broken image because the upload lives in `pmwiki_data/uploads/Class/119-bmw.png` but the link resolves to `assets/uploads/119-bmw.png`.

**Why it happens**: PMWiki stores uploads under `uploads/GroupName/filename`. The group name must be inferred from the page group (`Class.1` → group `Class`) unless the `Attach:` reference explicitly includes the group path.

**Solution**: When converting `Attach:filename`, look up the file in `uploads/[current_group]/filename` first, then fall back to `uploads/Main/filename`. Emit the correct relative path from the QMD file's location in `site/`.

### 5. `:if false:` Blocks Leaking Into Output

**Problem**: Hidden instructor notes or draft content (inside `(:if false:)...(:if:)`) appear in the rendered Quarto site.

**Why it happens**: A naive regex that strips `(:if false:)` and `(:if:)` tags without removing the content between them leaves the inner text unprotected.

**Solution**: Use a non-greedy multiline match that captures and discards everything between `(:if false:)` and `(:if:)`. Apply this rule first, before any other block-level rules. Test case in `pmwiki_quarto.json → validation.test_cases`.

### 6. GitHub Actions Fails with "Branch gh-pages does not exist"

**Problem**: The publish workflow errors on the first run because the `gh-pages` branch was never initialized.

**Why it happens**: `quarto-dev/quarto-actions/publish` expects the `gh-pages` branch to exist before it can push to it.

**Solution**: Run `cd site && quarto publish gh-pages` locally once to create the branch. After that, the Actions workflow handles all subsequent publishes. Document this as a one-time setup step.

### 7. Nested Toggle Blocks Break the Outer Regex

**Problem**: A `>>toggle<<` block that contains another `>>toggle<<` block causes the outer regex to close prematurely on the inner `>><<`, leaving the outer closing `>><<` as literal text in the output.

**Why it happens**: The non-greedy `.*?` in the toggle regex still closes on the first `>><<` it encounters, which is the inner block's close tag, not the outer one.

**Solution**: Log a warning and emit the raw block as a Markdown code fence for manual review rather than producing corrupted output. See `pmwiki_quarto.json → error_handling.known_failures` for the fallback behavior. In practice, the Math 119 wiki rarely nests toggles — this is primarily a guard against edge cases.

### 8. Unicode Decode Errors on Older Flat Files

**Problem**: A small number of PMWiki flat files (typically older pages) raise `UnicodeDecodeError` when read as UTF-8, despite declaring `charset=UTF-8` in their header.

**Why it happens**: PMWiki was not always strict about encoding. Pages created or edited in older versions may have Windows-1252 or Latin-1 bytes embedded in otherwise UTF-8 content — particularly in author fields or early comment text.

**Solution**: Open all flat files with `errors='replace'` so conversion continues rather than crashing. Log the page name and byte offset for manual inspection. The `text=` field itself is almost always clean — the problematic bytes usually appear in diff/history sections that are ignored anyway.

### 9. Alpha-Ordered Lists Losing Their Formatting

**Problem**: `#%25alpha%25` list items (lettered like a, b, c...) convert to plain numbered lists.

**Why it happens**: `%25` is the URL-encoding of `%`, so `#%25alpha%25` decodes to `#%alpha%` — a PMWiki CSS class annotation. Standard Markdown and Quarto have no native alpha-list syntax.

**Solution**: Convert `#%alpha%` prefixed list items to `<ol type="a"><li>` HTML blocks. Group consecutive `#%alpha%` lines into a single `<ol>` tag. See `pmwiki_quarto.json → markup_rules.alpha_list`.

---

## External System Lessons

### PMWiki Flat Files — Diff Sections After `text=`

**Behavior**: PMWiki flat files contain the current page text in the `text=` field, followed by revision history in `diff:timestamp:timestamp:=` fields. These diff fields also contain URL-encoded content that looks like page text.

**Why it matters**: A naive "find `text=` and take everything after it" parser will include all revision diffs in the conversion, producing hundreds of lines of garbage markup in the QMD output.

**How to handle it**: Extract only the value of the `text=` field — split the file on `\n` and find the line starting with `text=`. Take only that one line's value (everything after the first `=`). Stop there; do not read further into the file.

### Quarto GitHub Actions — `freeze` Directory Must Be Committed

**Behavior**: If any QMD files use `execute: freeze: auto` (for computational content), Quarto writes a `_freeze/` directory that caches execution results. The GitHub Actions runner won't re-execute Python/R, so it needs this cache committed.

**Why it matters**: Without `_freeze/` committed, any QMD with `#| eval: true` will silently produce empty output blocks in CI. Pure-markup QMD files (no code execution) are unaffected — this only matters if you later add executable code cells.

**How to handle it**: For a pure-markup math site like this one, add `execute: freeze: auto` to `_quarto.yml` and commit `_freeze/` if you ever add executable code. For the initial conversion (all markup, no code), this is not needed.

### PMWiki Pipe Tables — `||...||` Delimiter Format

**Behavior**: PMWiki's most common table format uses `||` delimiters, not `(:table:)`. Header cells use `||!text||` (exclamation mark, not `||#text||`). A table attribute row like `||border=1 width=80%||` (single cell matching `\w+=`) must be skipped — it's a style directive, not data.

**Why it matters**: `(:table:)` directives are stripped cleanly, but `||` tables survive unless there's a dedicated `convert_pipe_tables()` pass before inline rules. A regex applied to the full page text won't reliably handle the multi-row structure.

**How to handle it**: Process tables line-by-line before any inline rules. Collect consecutive `||`-starting lines into a row buffer; flush to a Markdown table when a non-`||` line appears.

### PMWiki — `[[#anchorname]]` Inline Anchor Definitions

**Behavior**: `[[#PP]]` in PMWiki creates an in-page anchor (like `<a id="PP"></a>`) that can be targeted by links like `[[#PP | Jump to PP]]`. The bare link handler (`[[...]]` → strip brackets) converts it to `#PP`, which then looks like a no-space ordered list item to the quality checker.

**Why it matters**: Without a dedicated anchor rule, `[[#anchor]]` at line start produces `#anchor` which corrupts ordered list detection and triggers false positive G2 quality alerts.

**How to handle it**: Add a rule before all other link rules: `\[\[#([A-Za-z][A-Za-z0-9_-]*)\]\]` → `<a id="\1"></a>`.

### PMWiki — `(:include:)` and `(:comment:)` Are Unconverted Directives

**Behavior**: `(:include Page.Name:)` is a server-side page transclude. `(:comment text:)` is a server-side comment that's invisible on the wiki but would appear as literal text in QMD output. Both survived the initial `strip_directives()` pass.

**Why it matters**: `(:include:)` directives are critical-severity leaks — students see raw `(:include Page.Something:)` text. `(:comment:)` blocks can span multiple lines with `%%` delimiters inside them.

**How to handle it**: Add to `strip_directives()`:
- `(:include ...:)` → `<!-- include: PageName -->` (HTML comment for traceability)
- `(:comment ....:)` with DOTALL → strip entirely (multiline, non-greedy)

### PMWiki — `\\` Forced Line Break

**Behavior**: `\\` at end of a line forces a line break in PMWiki. This is distinct from LaTeX `\\` (which appears inside math environments and is protected by placeholder extraction). The standalone `\\` at line end outside math produces literal `\\` in QMD.

**Why it matters**: Appears in 80+ places across the Math 119 pages, primarily in class pages with handwritten equation steps shown line-by-line. Renders as visible `\\` characters in the browser.

**How to handle it**: After math extraction (so placeholders protect LaTeX `\\`), apply: `\\\\\s*$` → `<br>` with `re.MULTILINE`. This is safe because all math `\\` are in placeholders at this point.

### PMWiki — `(:attachlist:)` Is a Server-Side Directive

**Behavior**: `(:attachlist:)` renders a dynamic list of attachments on the live PMWiki server. It has no static equivalent — the list is generated at request time by PHP.

**Why it matters**: Pages containing `(:attachlist:)` (typically `Main.HomePage`) will have a blank section in the converted output unless handled explicitly.

**How to handle it**: Replace `(:attachlist:)` with a static list of files found in the corresponding `uploads/GroupName/` directory during conversion. The converter script builds this list from the local filesystem.

---

## Validation and Testing

### Quick Validation
1. Convert `Class.1` only: `uv run python tools/pmwiki_to_quarto.py --page Class.1`
2. Open `site/class/class-1.qmd` — verify math is in `$...$`, headers are `##`, toggle is `<details>`, images reference `../assets/uploads/Class/`.
3. Run `quarto render site/class/class-1.qmd` — should produce HTML with no warnings.

### Comprehensive Validation
See `pmwiki_quarto.json → validation.test_cases` for:
- Before/after pairs for every markup rule
- Edge cases: math inside lists, nested toggles, `:if false:` blocks
- Navigation sort order check (Class.10 after Class.9)
- Broken-image detection (Attach: files that don't exist in uploads/)
- GitHub Actions YAML schema check

### Quality Bar
- [ ] All 68 pages (Class + Definition + Flex) convert without Python exceptions
- [ ] No raw PmWiki markup (`>>`, `(:`, `[[`, `Attach:`) appears in any rendered QMD output — verify with `uv run python tools/quality_check.py --strict`
- [ ] All LaTeX blocks render in `quarto preview` (no MathJax errors in browser console)
- [ ] Collapsible answer blocks work in browser (click expands, click collapses)
- [ ] All `Attach:` references resolve to existing files in `site/assets/uploads/`
- [ ] GitHub Actions publish workflow completes green on push to `main`

---

## Examples

### Example 1: Converting a Single Class Session Page

**Scenario**: Converting `Class.14` (a typical mid-semester class with Brain Gains problems, toggle answers, and a group discussion section) to QMD.

**Input** (decoded `text=` field, excerpt):
```
!! Brain Gains
1. Let $f(x) = \frac{2x+4}{x^2}$. Find $f(-4)$.
(:note:)
>>toggle<<
Answers
>>indent<<
#%alpha% $f(-4) = -0.25$
>><<
>><<
(:noteend:)
```

**Approach**: Agent calls `decode_pmwiki_file('pmwiki_data/wiki.d/Class.14')`, then `convert_pmwiki_to_qmd()` — math is extracted first, then the note block and toggle are converted, then inline rules run, then math is restored.

**Output** (`site/class/class-14.qmd`, excerpt):
```markdown
## Brain Gains

1. Let $f(x) = \frac{2x+4}{x^2}$. Find $f(-4)$.

::: {.callout-note}
<details>
<summary>Answers</summary>

<ol type="a"><li>$f(-4) = -0.25$</li></ol>

</details>
:::
```

**Code**: See `pmwiki_quarto.json → conversion_pipeline` for step order; `markup_rules` for each pattern.

---

### Example 2: Nested Toggle with `:if false:` Block

**Scenario**: A page with a hidden draft section (`(:if false:)`) followed by a toggle answer block — the draft must be stripped before the toggle is processed.

**Input** (decoded):
```
(:if false:)
Old version of the problem — remove before publishing
(:if:)
>>toggle<<
Answers
# $f(0)$ is undefined
>><<
```

**Approach**: `strip_if_false` rule runs first (step 2) and removes the hidden block entirely. Then `toggle_div` rule (step 3) converts the answer block. If order were reversed, the `:if false:` regex could match into the toggle content.

**Output**:
```markdown
<details>
<summary>Answers</summary>

1. $f(0)$ is undefined

</details>
```

**Code**: See `pmwiki_quarto.json → conversion_pipeline.rule_order` — `2_strip_if_false` before `3_block_rules`.

---

### Example 3: Full Pipeline Run

**Scenario**: Fresh semester — run the full sync + conversion + preview cycle after all 36 class sessions are finalized on the server.

```bash
# Step 1: Get latest from server
uv run pull_wiki.py

# Step 2: Convert all pages
uv run python tools/pmwiki_to_quarto.py

# Step 3: Preview locally before pushing
cd site && quarto preview

# Step 4: Push → GitHub Actions publishes to gh-pages
cd .. && git add site/ .github/ && git commit -m "Rebuild Quarto site from updated wiki" && git push origin main
```

**What the agent checks before writing**: confirms `pmwiki_data/wiki.d/` is non-empty, confirms Quarto CLI is installed, confirms `site/` output dir exists or can be created. See `pmwiki_quarto.json → error_handling.fallbacks`.

---

## Resources and References

### Agent Files
- **`pmwiki_quarto.json`**: Markup rules, tool definitions, `_quarto.yml` template, GitHub Actions template, validation cases
- **`tools/pmwiki_to_quarto.py`**: Conversion implementation
- **`pull_wiki.py`**: SFTP sync script (run before conversion)

### Related Agents
- `canvas_content_sync` — syncs content between Canvas courses; complementary to this agent (Canvas is delivery, Quarto site is reference)

### External Documentation
- [Quarto Website Docs](https://quarto.org/docs/websites/)
- [Quarto GitHub Pages](https://quarto.org/docs/publishing/github-pages.html)
- [quarto-dev/quarto-actions](https://github.com/quarto-dev/quarto-actions)
- [PmWiki Text Formatting Rules](https://www.pmwiki.org/wiki/PmWiki/TextFormattingRules)
- [PmWiki Markup Master Index](https://www.pmwiki.org/wiki/PmWiki/MarkupMasterIndex)

---

## Quick Reference Card

| Aspect | Value |
|--------|-------|
| **Purpose** | Convert PMWiki flat files → Quarto QMD site deployed to GitHub Pages |
| **Input** | `pmwiki_data/wiki.d/` (PMWiki flat files) + `pmwiki_data/uploads/` |
| **Output** | `site/` (Quarto project) + `.github/workflows/publish.yml` |
| **Agent Type** | `llm_agent` orchestrating a sequential conversion pipeline |
| **Complexity** | standard |
| **Key Files** | `pmwiki_quarto.json`, `tools/pmwiki_to_quarto.py`, `pull_wiki.py` |
| **Quickstart** | `uv run pull_wiki.py && uv run python tools/pmwiki_to_quarto.py && cd site && quarto preview` |
| **Common Pitfall** | Math expressions corrupted by list/bold rules — always extract math first |
| **Dependencies** | `quarto` CLI, `paramiko`, `python-dotenv`, GitHub repo with Pages enabled |
