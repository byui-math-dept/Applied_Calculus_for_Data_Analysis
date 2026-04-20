# Converter audit — cl-editorial-pilot

Session goal: make all 46 class QMDs render cleanly and match the live
wiki as the source of truth. CL editorial judgment pass is deferred for
human review.

## Headline numbers

| Audit                    | Before | After |
|--------------------------|-------:|------:|
| Structural (converter)   |   138  |    31 |
| Structural categories    |    8   |     1 |
| Content parity (vs wiki) |    36  |     0 |

The remaining 31 structural hits are all `\diff{}{}` macro *references*
across 8 pages; the macro is now defined in `site/_quarto.yml`, so those
render correctly (`\diff{u}{x}` → `\frac{du}{dx}` via MathJax).

## Commits on branch

```
a0ff436 Re-render site output from converter updates
a101543 Converter: resolve includes/template vars, normalize code blocks,
        define \diff macro
1c44a9b Converter: strip all (:if <cond>:)...(:if:) blocks (not just false)
```

## What the converter now handles

Added to `tools/pmwiki_to_quarto.py`:

- **Template variables** — `{$Name}`, `{$PageName}`, `{$Group}`, `{$Title}`
  resolved against the current page; any remaining `{$…}` stripped.
- **Includes** — `(:include PageName:)` now inlines the target page's
  converted body (definitions expand where they're used, wrapped as
  `<details>` via the target's own `>>toggle<<`).
- **Conditional blocks** — `(:if <cond>:)…(:if:)` fully stripped for any
  condition (was only stripping `false`). The public wiki renders nothing
  for `(:if auth admin:)` either; now QMDs match. **Biggest single fix.**
- **Code fences** — Fenced content is stashed as placeholders before any
  list/toggle/inline rules run and restored afterward. R comments like
  `# clear environment` no longer get corrupted into `1. clear environment`.
- **R language detection** — Auto-tags unadorned ``` blocks as ```r when
  content has R-distinctive signals (`<-`, `function`, `library(`, etc.).
- **Author typos** — `(:codemend:)` and `(:codend:)` normalized to
  `(:codeend:)` (44 occurrences across 10 class pages were cascading into
  broken toggle conversions).
- **Reverse-pipe links** — `[[url|text]]` now handled in addition to
  `[[text|url]]`.
- **`\diff` macro + `resources:` glob** — Emitted into generated
  `_quarto.yml` so PDFs and CSVs publish under `../assets/`.

## What's still per-page

`tools/after_class_N.py` scripts for one-off content that can't be
generalized. Current:
- `after_class_5.py` — Check blocks (list / HTML interleave) and bare
  Desmos URLs.

No new per-page scripts were needed in this session — every issue was
either a global rule (fixed in the converter) or author-source content
that's outside scope (math typos, runtime bugs in R snippets).

## Known author-source issues not touched

These are in the PMWiki source, not converter artifacts. Flagging for
the human editorial pass — deliberately not edited:

- `site/class/class-7.qmd` L35: `(2+6)^2` vs. `(2+6^2)` — likely math
  typo in the author's answer key.
- `site/class/class-7.qmd` L97: `## Discusion` — spelling ("Discussion").
- `site/class/class-33.qmd` L385: `p(7)` — `p` is a vector in that
  chunk, not a function; call will error at runtime.
- `site/class/class-33.qmd` L391: stray `### Compare to` *inside* an R
  code block — valid R (`###` is still a comment) but unusual. Leave
  alone unless Chaz wants to restyle it.

## Parity audit methodology

`/tmp/parity_audit.py` fetches each `https://byuimath.com/clarkc/all/119/index.php?n=Class.N`
(cached to `/tmp/wiki_cache/`), extracts the `<div id='wikitext'>` block
and strips code/math to the same rules applied to the QMD, and reports
heading diffs + token ratio.

- Heading diffs now zero across all 46 pages.
- Token ratios all in 0.98–1.34 (remaining skew is audit artifact: QMDs
  escape `$` as `\$` for money, wiki has literal `$` so the audit
  over-strips math-like spans on the wiki side).

The full converter audit (`/tmp/converter_audit.py`) checks 11
structural categories; 10 of 11 are at zero.

## Pipeline

```
uv run pull_wiki.py
uv run python tools/pmwiki_to_quarto.py
uv run python tools/apply_url_swaps.py   # NEW: enforces correct order
# per-page after_class_N.py scripts (currently only class 5)
python tools/generate_schedule.py
cd site && quarto render
```
