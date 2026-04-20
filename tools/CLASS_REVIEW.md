# Class Page Review — Punch List

Source-of-truth: live wiki at `https://byuimath.com/clarkc/all/119/index.php?n=Class.N`
(cached in `/tmp/wiki_cache/`). Converted QMDs at `site/class/class-N.qmd`. The
structural converter pass is clean; this document captures what still needs
human or scripted cleanup *after* the core converter rules run.

Three categories per class:

1. **Structural / render** — converter-shaped issues: mangled lists, broken
   `<details>`, missing code language tags, bare URLs, PMWiki artifacts, etc.
2. **Editorial / author** — issues in the original PMWiki source: typos, math
   errors, broken R calls, stale links.
3. **Cognitive load** (CL) — first-cut flags for the editorial pass. Flag
   generously; Chaz (instructor) will override. These cover overwhelming
   answer blocks, sections that want splitting, missing scaffolding.

## Methodology notes

- Each class was reviewed by one of five parallel subagents; this doc
  consolidates their findings.
- **False-positive caveat on "double backticks":** many pages were flagged
  for ``` `` ``` patterns. These are almost always legitimate Markdown
  inline-code-with-backtick-escape (`` ` `` delimiting content that
  contains a single backtick). Only worth investigating where accompanied
  by visibly-broken code fences — not a bulk cleanup target.
- **False-positive caveat on "ratio flags":** when an activity section
  mixes a lot of code/math with narrative, the word-count ratio between
  wiki and QMD can look alarming but the content is fully present
  (confirmed by spot-checks on classes 15, 23, 30, 33, 34). Treat any
  "ratio < 0.4" finding below as worth *verifying* before acting; several
  are false alarms from code-block handling.

---

# Per-class notes

## Class 1

**Structural:**
- (none noted)

**Editorial:**
- Line 58: "The number $f(3)$ an irrational number…" should be "The number
  $f(\sqrt{3})$ is an irrational number…" (missing "is", wrong argument).

**Cognitive load:**
- Brain Gains has 5 problems plus a "prove a property" task — substantial
  before group work. Consider frontloading the explanation about
  undefined vs. no solution before problem 1 answer.
- Problem 5's explanation is long; move detailed algebraic working into
  a separate collapsible "Deep Dive" inside the answer block.

## Class 2

**Structural:**
- (none noted)

**Editorial:**
- Line 18: "undefinded" → "undefined" (typo in wiki source).
- Discussion section "Mastery Learning" appears thin/absent in QMD; worth
  verifying against wiki.

**Cognitive load:**
- "Reading Definitions and Classifying Functions" has 8 nested `<details>`
  definitions before the classification table. Accordion fatigue. Add a
  brief intro sentence or group related definitions.
- Two identical tables (blank prompt + filled answer) run back-to-back;
  give them breathing room.

## Class 3

**Structural:**
- Several code examples use bare ``` ``` ``` fences without an `r` language
  tag (lines 155–176, 252); Quarto won't syntax-highlight these.

**Editorial:**
- Line 58–60: power-vs-exponential definition is dense; a side-by-side
  table would read better than prose using $u$/$v$.
- Line 178: Comment says `head(mtcars)` but never shows the output.

**Cognitive load:**
- "Plotting in R" subsection renamed from wiki's "Plotting with R" — keep
  naming consistent across references.
- Code escalates fast from `plot(x, x^2)` to `ifelse` piecewise functions.
  Insert a middle step (`type="l"` alone).
- Some functions are named with dots (`.p1a`) then referenced with
  underscores (`f.p1a` vs `f_p1a`) — **will error at runtime**.

## Class 4

**Structural:**
- Line 191: code block ends with `@]` and `(:codeend:)` PMWiki remnants;
  converter missed this one.
- Line 191: malformed line `plot(L,y,type='l',xlim=c(90,110), ylim = c(0,1))`
  followed by an unclosed syntax block.

**Editorial:**
- Line 35: "RMarkdown" vs "R Markdown" inconsistent capitalization.
- Line 33: references `f(x; m, b)` notation not introduced until Class 5.

**Cognitive load:**
- "Discussion - Create and Knit an RMarkdown" lacks an objective sentence.
- "Interactive Programming Activity" and "Activity - RStudio Practice"
  duplicate practice problems; unclear which students should do.

## Class 5

**Structural:**
- Line 17: typo in solution: `chose $8=2$` should be `chose $a=8$`.
- Lines 56–57: code block missing language tag.

**Editorial:**
- Line 17: confusing notation `$8=2$` — use `$a=8$` throughout.
- Line 33: solution cites `$a=2, b=1, c=5, d=-2$` but the problem has
  `$a=4, b=2, c=-3, d=7$` — misaligned answer.

**Cognitive load:**
- Parameter-exploration exercises would benefit from a visual showing how
  $T(x) = af(b(x+c))+d$ maps to shift/scale.
- "Repeat parts A-E for $f_3(x) = 1/x$" referenced in classes 2 & 3 but no
  solutions provided; students may abandon.

## Class 6

**Structural:**
- Lines 52–67: code blocks use bare ``` ``` ``` without `r` tag.

**Editorial:**
- (none noted beyond whitespace.)

**Cognitive load:**
- "Activity - Transformations" references Desmos + Project Unit 1 link
  but endpoint isn't rendered in QMD; students must build the URL.
- Explain *why* default parameters matter before showing `f_quad1` vs
  `f_quad2`.

## Class 7

**Structural:**
- Line 145: `Discusion` → `Discussion` (typo).
- Line 36: solution shows exponent `$(2+6)^2$` but context suggests
  `$(2+6^2)$` — verify against wiki.

**Editorial:**
- Line 113: "Give an interval on which $f$ is both increasing and
  decreasing" is contradictory; likely meant "has both increasing and
  decreasing regions" or "constant."

**Cognitive load:**
- "Describing Functions" has 6 nested `<details>` definitions before
  example application — same accordion fatigue as Class 2.
- "Systems of Equations" jumps from 2-variable concrete to
  `$a, b, c, d, e, f$` abstract in 8 steps; intermediate scaffolding
  would help.

## Class 8

**Structural:**
- Line 191: code block has residue `@]` + `(:codeend:)` + raw bullet
  markup (`* What did you notice…`) from PMWiki. **Will break render.**
- Line 113 vs 143: duplicate "Summary" headings (one at H4, one added as
  "Summary Plots") — document outline gets confused.
- Lines 204/224/242: placeholder `[your selected value]` is correct
  pedagogy but line 191 has extra debris.

**Editorial:**
- **Significant content loss**: "Function Mad Libs" section is 99 words
  in QMD vs 241 in wiki. QMD retains only bare template ("Quantity 1:",
  "Quantity 2:"); the narrative examples that make the exercise
  meaningful are gone. The "Function tells a story" lesson is neutered.

**Cognitive load:**
- Restore "Mad Libs" examples or add a worked example (e.g., "If x is
  'time in weeks' and y is 'remaining battery %', tell the story of
  $y = 10 - \sqrt{x+4}$").
- "Summary Plots" mixes discussion prompts with placeholder code —
  separate the two.

## Class 9

**Structural:**
- (none noted.)

**Editorial:**
- Line 30: answer code is correct but phrasing "grows by 5 each year to
  reach 110 in 2020" could read more clearly as "grows at 5 elves per
  year, reaching 110 in 2020 (20 years after 2000)".
- Lines 183–187: "Activity - Logs with $\prod$ and $\sum$ notation" has
  prompts but no solutions / worked examples.

**Cognitive load:**
- "Definitions and Reminders" is 7 back-to-back `<details>` blocks
  (Exponential, Properties of Exponents, Logarithm, …). Move to a
  Reference appendix and introduce on-demand.
- Provide at least one worked example for the log-of-product activity:
  $\ln(\prod_{m=1}^3 (mx+1)) = \ln(x+1) + \ln(2x+1) + \ln(3x+1)$.

## Class 10

**Structural:**
- (none noted.)

**Editorial:**
- Line 227: stray text "I may call on people to the share in class."
  inside a code comment — remove or clarify.

**Cognitive load:**
- (none noted.)

## Class 11

**Structural:**
- Lines 70 & 74: bare PMWiki directives `@]`, `(:codeend:)`, `(:code:)[@`
  leaked into output — converter missed this page (likely a `:codemend:`
  typo variant not covered yet).

**Editorial:**
- (none noted.)

**Cognitive load:**
- (none noted.)

## Class 12

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- (none noted.)

## Class 13

**Structural:**
- Line 70: double closing backtick inside a code fence.

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Activity - Practice with Probability" has 4 Examples with answers in
  deeply nested `<details>`. Lifting answers to the same heading level
  as questions would reduce nesting depth and improve scanability.

## Class 14

**Structural:**
- (none noted.)

**Editorial:**
- **Content truncation**: "Activity - Florida Tropical Storms Revisited"
  (lines 69–119) is much shorter than wiki. QMD shows setup, code, and a
  stub for "Additional Calculations and Questions"; wiki includes the
  full walkthrough of the Poisson process.
- Line 173: wiki URL `https://en.wikipedia.org/wiki/List_of_Florida_hurricanes_(200080%93present)`
  has mangled percent-encoding (`80%93` should be `–` i.e. an en-dash,
  so the path is `(2000–present)`). Will 404.

**Cognitive load:**
- Answer blocks sit *immediately* after prompts within the same
  `<details>`. Encourages peeking before attempting.

## Class 15

**Structural:**
- Lines 8–9: image URLs inside `<...>` autolinks —
  `<https://byuimath.com/bmw/all/119/uploads/Class/f5-fit1.png>` —
  this renders as a link, not an embedded image.
- Line 94: broken autolink `<https://chaz-clark.github.io/M119/Projects/unit1.html.>`
  — trailing period inside the angle brackets.

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Deterministic vs Probability Models" (lines 252–273) is a long list
  of examples with no synthesis. Close with a sentence tying back to the
  modeling focus.

## Class 16

**Structural:**
- Lines 283, 315: empty code-block placeholders (`m1 <-` etc.) for
  students to fill in — intentional, flag for confirmation only.

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Introduction to Linearization" has three nested code blocks and an
  "alternate version" with a custom function. Give students explicit
  guidance on which version to use when.

## Class 17

**Structural:**
- Line 41: PDF autolink `<../assets/docs/DerRules_Power_Constant_Sum.pdf>`
  — should be `[Derivative rules](../assets/docs/DerRules_Power_Constant_Sum.pdf)`.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Lines 43–57: 8 derivative practice problems with no worked example
  first. Add one annotated derivation citing the rules.

## Class 18

**Structural:**
- Line 170: PDF autolink — see Class 17 (same pattern).

**Editorial:**
- Line 92: "remember to *pass the chalk* after **theses** problems" —
  `theses` → `these`.

**Cognitive load:**
- Problem 10 (line 110) tells students "search online for a tool that
  will compute derivatives" in place of working it out. Undermines the
  pedagogy — provide the worked solution instead.

## Class 19

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Activity - Compute derivatives" (10 problems, lines 121–141) has no
  worked example before the drill. Brain Gains solutions don't show
  step-by-step work. Add a fully annotated problem 1 with all rules
  cited.

## Class 20

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- Lines 45–52: "Activity - Chain Rule" items numbered 1 through 5 all
  start with `1.` — will render as a single-item list restarting each
  time. Renumber or let the author intent drive markdown numbering.
- Line 59: PDF autolink `<../assets/docs/Higher_Order_Derivatives.pdf>` →
  real markdown link.
- Lines 175–189: answer blocks use mixed numbering that's confusing
  against the question numbers.

## Class 21

**Structural:**
- Lines 39–48: Desmos autolinks `<https://www.desmos.com/calculator/...>`
  should be `[Desmos: …](https://www.desmos.com/calculator/...)`.

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Activity - Practice with the Chain rule" (lines 108–135) lists 15
  function-pair problems back-to-back with no intermediate scaffolding.

## Class 22

**Structural:**
- Line 29: image URL `<http://byuimath.com/bmw/all/119/uploads/Class/chain_rule_exercise.png>`
  renders as autolink, not embedded image.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains (lines 10–66) packs 4 numbered problems including
  summation manipulation with no warm-up or preview.

## Class 23

**Structural:**
- Line 59: PDF autolink (same pattern as 17/18/20).
- "Activity - Derivative Practice" ratio 0.35 (wiki 140 words vs QMD 49).
  Verify whether worked inline examples were intentionally moved to the
  linked PDF, or if content was dropped.

**Editorial:**
- The Activity is now a stub linking to a worksheet PDF; wiki had inline
  examples with full answers. Either restore the inline versions or add
  a one-line summary of what the worksheet covers.

**Cognitive load:**
- "Higher order derivatives" and "Chain Rule Practice" subsections are
  both under "Derivative Practice" but function as independent
  activities; students won't know where to focus.

## Class 24

**Structural:**
- Lines 26, 67–69: R code blocks missing `r` language tag.
- Line 82: PDF autolink pattern again.
- Line 82: second code block opens with ```` ```r ```` but content
  formatting suggests unclosed fence — verify render.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains opens with distance-to-hyperbola optimization, then
  R graphing, then uniroot across three sub-problems with no unified
  solution. Big difficulty spike.
- "Loglikelihood Practice…" activity is multi-part with heavy R and
  calculus interleaved; restate the overall goal up front.

## Class 25

**Structural:**
- Line 24: PDF autolink pattern.
- Line 161: same.
- Lines 27–140: "Theorems - Tests - Definitions" is **16 collapsed
  `<details>` blocks, all labeled `Solution`/`toggle`**. No visual cue
  to distinguish them without opening each.

**Editorial:**
- (none noted.)

**Cognitive load:**
- The 16-details wall should become a table or quick-reference card.
- "Activity - Comparing Solutions" references an external worksheet and
  then lists all 16 theorems; unclear whether the worksheet is
  prerequisite or supplement.

## Class 26

**Structural:**
- Lines 97–137: R code fence alignment / indentation may glitch the
  render — verify visually.
- 48 "double-backtick" flags — almost certainly inline-code-with-backtick
  markers; verify no real issue.

**Editorial:**
- Lines 96–105: `my_plot`/`my_lines` are custom functions but not framed
  as such; students may think they're built-in.

**Cognitive load:**
- Lines 96–117: many variations and optional parameters before the
  basic plotting idea is solid.

## Class 27

**Structural:**
- Lines 109–112: inline escaped characters / PMWiki stray markers —
  verify render.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains (lines 17–100) runs 3 progressively complex
  system-of-equations problems; by #3, students are juggling summation
  notation and system-solving simultaneously with no reflection gap.

## Class 28

**Structural:**
- Lines 131–158, 247–275: code fences may lack language tag or have
  broken wrapping.
- Line 197: `->You have...` arrow remnant — verify render.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains jumps from system-hint straight to finding `a_1` for
  loglikelihood with no intuition bridge.
- Three "Maximizing …" subsections live under Group Meeting with no
  task headers; the last is mostly copy-paste code without narrative.

## Class 29

**Structural:**
- (none noted.)

**Editorial:**
- Line 8: "that id defined" → "that is defined".

**Cognitive load:**
- Brain Gains packs 3 definition boxes + substantial problem work
  before Group Meeting.
- Activity moves from definitions to full 2D optimization with data
  in one jump.

## Class 30

**Structural:**
- Lines 203–360: "Activity - More Practice with Maximum Likelihood
  Method" has the headings but the problem statements, code, and
  guidance are absent (35 words QMD vs 319 wiki). Students see only
  section titles. **Verify this is not a converter drop** before
  assuming author intent.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains is ~530 words with many nested details before any
  practice — front-loaded.
- The three subsections under "Activity - More Practice" lack any
  introductory prose explaining the progression.

## Class 31

**Structural:**
- Line 8: dangling `1.` at the top of Brain Gains.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains opens with heavy calculus (partial derivatives on
  3-variable function + Hessian determinant) with no modeling context.

## Class 32

**Structural:**
- Line 53: `c_{1.2}` should be `c_{1,2}` (subscript typo).

**Editorial:**
- Line 158: "using either the Least Squares or or Maximum Likelihood
  method" — duplicate `or`.

**Cognitive load:**
- "Activity - Compare loglikelihood and least squares" is heavily
  abbreviated in QMD (46 words vs 190 wiki) — **verify content wasn't
  dropped**.
- Summary (lines 201–241) is a dense philosophical discussion;
  consider splitting.

## Class 33

**Structural:**
- "Grab one ball" activity has 4-level heading nesting — confusing for
  the document outline.
- 34 double-backtick flags — likely false positive (inline code).

**Editorial:**
- Line 385: `p(7)` — `p` is a probability vector defined above, not a
  function. Should be `p[7]`. **This R call errors at runtime.**

**Cognitive load:**
- "Activity - Balls in a Bag" collapsed to 60 words (QMD) vs 376 words
  (wiki). **Verify content wasn't dropped.**
- Discussion section is 52–53 lines of vocabulary review — very dense
  for a debrief.

## Class 34

**Structural:**
- Lines 48–162: "Activity - Targets for Continuous Random Variables"
  shows three subsection headers (Rectangular, Triangular, Parabolic
  Spandrel) with almost no prose — 48 words QMD vs 530 words wiki.
  **Verify.**

**Editorial:**
- (none noted.)

**Cognitive load:**
- Students hit three target shapes with no introductory framing.
- Brain Gains is very short (~130 words); Group Discussion asks
  students to share prep with no concept summary first.

## Class 35

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains opens with vocabulary recap then 4 solved examples — no
  scaffolding on *how* to approach target normalization.
- Group Meeting sections 2 and 3 are near-duplicate practice problems;
  vary the prompt or explain what changes.

## Class 36

**Structural:**
- (none noted.)

**Editorial:**
- Line 229: awkward line break between "What happens when we increase
  $n$?" and the bold text that follows.

**Cognitive load:**
- "Practice with identifying PDFs" gives 5 example functions but only
  the first 2 have explicit solutions shown; students must infer.
- Brain Gains covers 2 PDF properties + uniform distribution then
  jumps to a complex grid-table task with no explicit connection.

## Class 37

**Structural:**
- Line 45: `## Dicsussion` → `## Discussion` (creates a duplicate
  heading, since the correctly spelled `## Discussion` exists at 294).

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains asks students to verify 2 PDF properties + compute a
  normalization constant `k` without first showing an example.
- "Riemann Sums with R, Definite integrals with Mathematica" is ~180
  lines with many inline code blocks; students must track between R
  approximations and Mathematica exact integrals without signposting.

## Class 38

**Structural:**
- (none noted.)

**Editorial:**
- Line 168: `\int_{-\infty}^{1} f(x)dx \neq \int_{-\infty}^1 \frac{1}{18}(9-x^2)dx`
  — uses `\neq` while the rest of the page uses plain `=`/`<`/`>`
  (inconsistent tone only, math is right).

**Cognitive load:**
- Brain Gains (lines 124–220) has 11 nested exercises before answers.
  Add signposting or split "Repeat the above" into its own section.

## Class 39

**Structural:**
- (none noted.)

**Editorial:**
- Line 79: `The Methos of Moments` → `Method of Moments`.
- Line 27: centroid URL — verify rendering in Quarto output.

**Cognitive load:**
- "Using our fitted models" (lines 235–311) has 4 sub-problems with
  yellow-highlighted motivations in wiki; those highlights render as
  plain text in QMD.

## Class 40

**Structural:**
- Line 20: `$f(x) = \lambda e^(-\lambda x)$` — check rendering;
  parenthesized exponent is unusual LaTeX.

**Editorial:**
- (none noted.)

**Cognitive load:**
- "Activity - More Practice with finding PDFs, Expected Value,
  Variance, and CDF" spans lines 87–196 with 5 major problems each
  with multiple sub-parts. Signpost which are optional.

## Class 41

**Structural:**
- Line 78: code block may be missing its closing fence — verify.

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains problem 1 (lines 9–20) has 8 sub-questions (a–h) before
  Group Meeting. Split into two problems or label mandatory vs
  exploration.

## Class 42

**Structural:**
- Lines 93–98: bare PMWiki `:codem:` and `:codeend:` directives
  leaked through — converter missed this variant of the typo.

**Editorial:**
- Line 34: "A percentile divides ordered values (outcomes of a random
  variable) into 100 equal groups (per 100)." — redundant.

**Cognitive load:**
- "Calculate a Percentile" (lines 23–72) transitions abruptly from
  formal definition to 3 examples using different methods (CDF-based,
  PDF-based, numerical) without signposting the method shift.

## Class 43

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains + Group Meeting + Discussion together span ~280 lines
  with overlapping problem sets (e.g., "Definite Integrals and
  Geometric arguments" appears in both Brain Gains and group work).
  Clarify individual vs collaborative.

## Class 44

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains (lines 7–18) and Group Meeting (lines 22–33) **contain
  the same CDF/PDF problems numbered 1–2 and 1–2**. Merge, or label
  clearly as "warm-up" vs "group activity."

## Class 45

**Structural:**
- (none noted.)

**Editorial:**
- (none noted.)

**Cognitive load:**
- Summary (lines 67–166) is dense — 5 `<details>` + inline
  definitions. Consider splitting to a "Key Ideas Summary" page or
  adding visual hierarchy.

## Class 46

**Structural:**
- Table at lines 22–54 uses Markdown table syntax — verify it renders
  correctly in Quarto (structure looks right).

**Editorial:**
- (none noted.)

**Cognitive load:**
- Brain Gains (lines 6–20) mixes probability calculation, FTC, 
  indefinite integrals, and matching in 8 consecutive problems without
  thematic grouping. Break into "Part A: Probability & FTC" and
  "Part B: Indefinite Integrals".

---

# Cross-cutting patterns

These are patterns that showed up across ≥3 pages. Each one is a candidate
for a global converter rule, a post-conversion script, or a
search-and-fix editorial pass.

## A. Converter-fixable (would reduce per-page work the most)

**A1. Autolink → Markdown link for non-URLs.** Many pages use `<...>`
autolinks around PDF paths (`<../assets/docs/X.pdf>`), image URLs
(`<http://.../foo.png>`), or Desmos links. Autolinks render as "click to
open" but lose the link text — Quarto users expect descriptive labels.
Pages affected (non-exhaustive): 15 (images), 17, 18, 20, 21, 22, 23, 24,
25. **Fix**: converter rule — where `[[X -> Y]]` had a *path-like* Y, emit
`[X](Y)` instead of `<Y>`; for image paths ending in `.png`/`.jpg`, emit
`![X](Y)`.

**A2. Stray PMWiki directives after `:codemend:`/`:codend:` fix.**
Classes 11 and 42 still have bare `@]`, `(:codeend:)`, `(:code:)[@`, or
`:codem:` leaking. These are variant typos I didn't catch; the current
converter normalizes `:codemend:` and `:codend:` but not `:codem:`. Also
Class 8 line 191 has the full PMWiki sequence intact — worth tracing
what about that block defeated the placeholder-restore.

**A3. Bare ``` ``` ``` fences with R content.** Converter auto-tags R
fences via signal detection (`<-`, `function`, etc.) but still misses
some — Classes 3, 4, 5, 6, 24, 28 each have at least one unadorned fence
with obvious R content. Candidate: expand the signal set (e.g.
`rm(list=ls())`, `par(mar=`, `read.csv(`, `seq(`, single-letter
`<-` assignments).

**A4. Duplicate / mis-cased headings.** Class 7 `Discusion`, Class 37
`Dicsussion` — both produce duplicate-named H2 sections. **Not a
converter bug** (they're in the source), but a post-conversion linter
would catch them via the structural audit.

## B. Editorial / author-source (Chaz-level)

**B1. Answer-reveal timing.** Across Classes 9, 13, 14, 16, 19, most
Brain Gains prompts have their full answer in a `<details>` immediately
below the question. Some students will peek. **Recommendation**: group
all answers into a single `<details>` at the end of each section, or
move to a separate "Answers" page, so the cognitive barrier to peeking
is higher.

**B2. Worked examples absent before drill sets.** Classes 17 (8 deriv
problems), 19 (10 deriv problems), 21 (15 chain-rule pairs), 35 (normalizations),
37 (PDF verification), 40 (5-problem PDF activity). In each, the first
worked example lives in Brain Gains but isn't framed *as* a worked example
for the drill that follows. One-line callout ("Use the technique from
Brain Gains problem 2 as your template") would bridge this.

**B3. Duplicated or overlapping problem sets between sections.** Class
23 (Derivative Practice contains two independent activities), Class 28
(Maximizing sub-sections nested under Group Meeting), Class 43 (same
integrals appear in Brain Gains + group work), Class 44 (Brain Gains
and Group Meeting share the same numbered problems). Pattern: old
wiki authoring didn't strictly separate individual-prep from
group-work; QMD inherits the ambiguity. **Fix**: rename sub-activities
or add a prefix (`Prep:` vs `Together:`).

**B4. Runtime-broken or runtime-suspicious R.**
- Class 3: dot-vs-underscore function naming inconsistency.
- Class 33 line 385: `p(7)` where `p` is a vector (should be `p[7]`).
- Others not flagged but worth a systematic R lint pass with
  `lintr::lint_dir("site/class")` after extracting code chunks.

**B5. Small typos in source.** `undefinded` (C2 L18), `Discusion` (C7
L145), `theses` (C18 L92), `Methos` (C39 L79), `id defined` (C29 L8),
`Dicsussion` (C37 L45), `or or` (C32 L158), `chose $8=2$` (C5 L17),
duplicate `c_{1.2}`/`c_{1,2}` (C32 L53). Fixable in one sweep.

## C. Cognitive load — high-level observations

**C1. Accordion fatigue.** Classes 2 (8), 7 (6), 9 (7), 25 (16) have
long runs of `<details>` definitions or reference blocks before
students meet the activity. Either (a) move definitions to a course
reference appendix, or (b) introduce each definition *just before* it's
first used.

**C2. Activity sections that look like stubs.** Classes 23, 30, 32, 33,
34 have one or more activity sub-sections where QMD prose is much
shorter than the wiki equivalent — ratios in the 0.1–0.4 range. **Verify
first**: the ratio drop may be from code being stripped from the word
count on the QMD side. But at least Classes 23 and 34 look like real
content was compressed to a heading + PDF reference. If intentional,
add a one-sentence orientation; if not, restore from wiki.

**C3. Front-loaded Brain Gains before any group work.** Classes 22, 24,
27, 28, 30, 31, 36, 38, 43 have Brain Gains that spans 200–500 words
with multiple compounding problems. Many run 3–11 consecutive prompts
with answers in immediate `<details>`. A typical student would spend
most of class time on Brain Gains before reaching Group Meeting. If
this is intentional (designed for pre-class prep), a visible label at
the top of each Brain Gains would help: *"Do these BEFORE class."*

**C4. Difficulty spikes with no bridge.** Same optimization-unit
classes (24, 27, 28, 31) escalate from single-variable to
multi-variable work inside one class period. A visible "reminder of
what we're tracking" sentence at each transition would ground students.

**C5. Significant content loss in Class 8 "Function Mad Libs".** Called
out separately because it's the only clear case where converter output
keeps headings but drops the pedagogical substance (narrative examples
that make the exercise meaningful). Restoration needed.

---

# Suggested next actions

**Script candidates** (mechanical, safe to automate):
1. Autolink → Markdown link conversion for PDF/image/Desmos paths (A1)
2. Expand R-signal detection in converter to catch more bare fences (A3)
3. Handle `:codem:` variant typo (A2)
4. Search-and-fix editorial typo sweep (B5)
5. Post-conversion lint: flag duplicate/near-duplicate H2 headings (A4)

**Agent / human editorial tasks** (judgement required):
1. Verify content-loss candidates: Classes 8, 14, 23, 30, 32, 33, 34 —
   confirm which are intentional compression vs real drops, and restore
   where needed. This is the highest-leverage pass.
2. Rename sub-activities where Brain Gains / Group Meeting overlap
   (B3) — small, reversible, improves navigation.
3. CL pass per Chaz's original ask — C1–C4 are the first cut; the
   instructor's judgement determines which are real issues and which
   are intentional design.

**Deferred / out of scope**:
- Rewriting R content (C3's `p(7)` and similar) — runtime fix belongs
  with the instructor, not with automation.
- Answer-reveal restructuring (B1) — requires pedagogical decisions.
