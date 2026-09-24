# User Guide source

This folder is the editable source for the in-app User Guide
(`Help → User Guide`, opened from `src/pps/ui/help/user_guide.html`).

**Do not hand-edit `src/pps/ui/help/user_guide.html`** — it is generated.
Edit the Markdown files here and rebuild.

## Layout

- `sections/NN_name.md` — one file per section, in TOC order (the `NN`
  prefix controls ordering). Each starts with a small frontmatter block:

  ```
  ---
  id: overview       # anchor id, used in the URL and cross-links
  number: 1          # shown as the numbered badge next to the title; omit for unnumbered sections
  title: Overview    # section heading
  ---
  Body in Markdown (headings become <h3>, tables use GFM `| a | b |` syntax).
  ```

  A section can instead set `raw: true` (no `title`) to be inserted as
  literal HTML with no wrapping — used for the safety-warning box and the
  contact card, which are fixed layouts, not prose.

- `images/*.png` — screenshots, referenced from a section with a fenced
  `figure` block:

  ````
  ```figure
  image: overview_main_window.png
  caption: Caption text, **bold** allowed.
  ```
  ````

  To update a screenshot, just replace the PNG file in `images/` — no
  markup changes needed. Filenames are descriptive on purpose so it's
  obvious which screen each one belongs to.

- `template.html` — the page shell (CSS, header, TOC wrapper). Only edit
  this for site-wide layout/style changes.

- `build_manual.py` — reads `sections/*.md` + `template.html`, converts
  Markdown to HTML, and writes `src/pps/ui/help/user_guide.html` plus a
  copy of `images/` at `src/pps/ui/help/images/`.

## Rebuilding

```bash
python docs/manual/build_manual.py
```

Requires the `markdown` package (`pip install markdown`, already listed
in `requirements.txt` as a dev-only dependency — it is not imported by
the app itself, only by this build script).

## Regenerating screenshots

The six screenshots under `images/` were captured from the previous UI
and need retaking against the current interface. Capture each one at a
reasonable window size, save as PNG with the same filename it already
has (or update the `image:` field in the relevant section if you rename
it), and rerun the build script above.
