# Math 119 Course Site — Faculty Guide

This site is built from the course PMWiki and published automatically to GitHub Pages. This guide covers everything a faculty member needs to maintain, update, and adjust the site — no programming experience required for most tasks.

---

## How the site works (big picture)

```
PMWiki server  →  pull_wiki.py  →  pmwiki_data/   (local copy)
                                        ↓
                               pmwiki_to_quarto.py  →  site/   (Quarto source)
                                        ↓
                               GitHub Actions   →  GitHub Pages  (live website)
```

- **The wiki is still the source of truth.** Edit content on the wiki; run a sync to pull it down; rebuild the site.
- **The schedule is separate.** It lives in `schedule_config.yml` and is updated by a daily GitHub Action — no wiki edit needed.
- **GitHub Actions publishes automatically.** Every push to `main` triggers a rebuild. The daily schedule update also triggers a rebuild at 8am MT.

---

## Common tasks

### View the live site
The site is at: `https://miniature-adventure-g44yz51.pages.github.io`

> **Custom domain planned.** A shorter URL (e.g. `byui-m119.github.io`) requires a dedicated GitHub org or user with that name. See the domain setup section below.

### Adjust today's class (slow down / speed up pacing)

Edit `schedule_config.yml` in the repo root. The `sessions:` list maps class meetings to sessions in order. Each line is one class day.

**To repeat a session** (e.g., need another day on Class 14):
```yaml
sessions:
  ...
  - class-13
  - class-14   # day 1
  - class-14   # day 2 — add this line
  - class-15
  ...
```

**To insert a project or review day:**
```yaml
sessions:
  ...
  - class-20
  - project    # shows "Project Work Day" on the home page
  - class-21
  ...
```

**To add a last-minute holiday or cancellation:**
Add the date to the `holidays:` section:
```yaml
holidays:
  - date: "2026-05-25"
    name: "Memorial Day"
  - date: "2026-06-10"    # ← add this
    name: "Department Meeting — No Class"
```

After editing `schedule_config.yml`, commit and push — the site rebuilds automatically within a few minutes.

### Sync new wiki content to the site

After editing class pages on the PMWiki:

```bash
# 1. Pull latest from server
uv run pull_wiki.py

# 2. Rebuild the QMD files from the wiki
uv run python tools/pmwiki_to_quarto.py

# 3. Commit and push → GitHub Actions publishes the site
git add site/ && git commit -m "Sync wiki updates" && git push origin main
```

### Rebuild a single page (faster)

If you only changed one or two wiki pages:
```bash
uv run pull_wiki.py
uv run python tools/pmwiki_to_quarto.py --page Class.14
git add site/class/class-14.qmd && git commit -m "Update Class 14" && git push
```

### Add board photos or class notes

1. Drop the image files into `site/assets/notes/`
2. Reference them in the relevant QMD file — for example, in `site/class/class-14.qmd`:
   ```markdown
   ![Board work from class](../assets/notes/class14-board.jpg)
   ```
3. Commit and push.

These changes won't be overwritten when you re-sync the wiki (the converter only touches `site/class/`, `site/definitions/`, `site/flex/`, and `site/schedule.qmd`).

### Preview the site locally before pushing

```bash
cd site && quarto preview
```

Opens a local browser at `http://localhost:4848`. Changes to `.qmd` files hot-reload.

---

## File map

| File / Folder | What it is | Edit it? |
|---|---|---|
| `schedule_config.yml` | Semester schedule — dates, holidays, session order | ✅ Yes — adjust pacing here |
| `pmwiki_data/wiki.d/` | Local copy of PMWiki pages | ❌ Never — overwritten by sync |
| `site/class/class-N.qmd` | Converted class session pages | ❌ Re-generated from wiki |
| `site/definitions/` | Converted definition pages | ❌ Re-generated from wiki |
| `site/flex/` | Flex day pages | ❌ Re-generated from wiki |
| `site/assets/notes/` | Board photos, extra notes | ✅ Add files here manually |
| `site/assets/uploads/` | Images from the wiki | ❌ Copied from pmwiki_data |
| `site/index.qmd` | Home page | ✅ Edit the welcome text |
| `site/_today.qmd` | Auto-generated "today's class" | ❌ Overwritten daily by GitHub Actions |
| `site/styles.css` | Site appearance | ✅ Edit to change colors/fonts |
| `site/_quarto.yml` | Navigation and site config | ✅ Edit to add pages or change theme |
| `tools/pmwiki_to_quarto.py` | Wiki → QMD converter | ❌ Code — don't edit |
| `tools/generate_schedule.py` | Schedule generator | ❌ Code — don't edit |
| `.github/workflows/` | GitHub Actions automation | ❌ Code — don't edit |

---

## How math works

The wiki uses LaTeX notation (`$f(x) = x^2$`, `$$\frac{d}{dx}...$$`) and the site preserves it exactly. Quarto renders it in the browser using MathJax — the same engine used by most math publishing tools. No conversion happens; the LaTeX passes through untouched.

Inline math: `$f(x) = x^2$` → renders as $f(x) = x^2$

Display math:
```
$$\int_0^1 f(x)\,dx$$
```
renders as a centered equation.

---

## How answer toggles work

The wiki's collapsible answer sections (`>>toggle<<`) become HTML `<details>` blocks on the site. Students click to reveal answers — same behavior as the wiki, no server needed.

---

## Troubleshooting

**Site didn't update after I pushed.**
Check the Actions tab on GitHub — look for a failed `Publish Quarto Site` job. The most common cause is a QMD syntax error. Run `quarto render site/` locally to find it.

**Today's class is wrong on the home page.**
The daily action runs at 8am MT. If it's before 8am or the action failed, run it manually: GitHub → Actions → `Daily Schedule Update` → `Run workflow`.

**I changed `schedule_config.yml` but the site still shows the old class.**
Make sure you committed and pushed the file. The publish workflow only triggers on push to `main`.

**A wiki page didn't convert correctly.**
Run `uv run python tools/pmwiki_to_quarto.py --page Class.N --dry-run` to see the output. If it looks wrong, report it — the converter may need a rule update for that page's markup.

---

## Setup (first time on a new machine)

```bash
# 1. Clone the repo
git clone https://github.com/chaz-clark/m119_master.git
cd m119_master

# 2. Install dependencies
uv sync

# 3. Copy .env and fill in credentials
cp .env.example .env
# Edit .env: add SFTP credentials and Canvas API token

# 4. Pull the wiki
uv run pull_wiki.py

# 5. Build the site
uv run python tools/pmwiki_to_quarto.py

# 6. Preview
cd site && quarto preview
```

Quarto must be installed separately: [quarto.org/docs/get-started](https://quarto.org/docs/get-started/)
