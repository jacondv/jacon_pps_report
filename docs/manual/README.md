# User Guide source

This folder is the editable source for the in-app User Guide, available
from `Help` as HTML (`Help → User Guide`, `src/pps/ui/help/user_guide.html`)
and as a printable PDF (`Help → User Guide (PDF)`,
`src/pps/ui/help/User_Guide.pdf`) — a copy of the PDF is also kept at
`docs/manual/User_Guide.pdf` for reference outside the app.

**Do not hand-edit `src/pps/ui/help/user_guide.html` or `User_Guide.pdf`**
— both are generated. Edit the Markdown files here and rebuild.

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

- `template.html` — the page shell for the in-app HTML guide (CSS, sticky
  sidebar TOC, header). Only edit this for site-wide layout/style changes.

- `template_pdf.html` — a separate, single-column/print-friendly shell used
  only for the PDF (no sticky sidebar — that doesn't paginate). Keep its
  section/table/callout styling in sync with `template.html` if you change
  one, since both render the same section content.

- `build_manual.py` — reads `sections/*.md` + both templates, converts
  Markdown to HTML, and writes:
  - `src/pps/ui/help/user_guide.html` + `src/pps/ui/help/images/` (HTML guide)
  - `src/pps/ui/help/User_Guide.pdf` + a copy at `docs/manual/User_Guide.pdf`
    (rendered via the `wkhtmltopdf` binary already vendored at
    `src/pps/report/packages/wkhtmltox/` for PDF report export; the PDF step
    is skipped with a warning if that binary isn't present)

## Rebuilding

```bash
python docs/manual/build_manual.py
```

Requires the `markdown` package (`pip install markdown`, already listed
in `requirements.txt` as a dev-only dependency — it is not imported by
the app itself, only by this build script) and `pdfkit` (already a runtime
dependency, used for PDF report export too).

## Updating screenshots

To refresh a screenshot, replace the PNG file in `images/` with the same
filename (or update the `image:` field in the relevant section if you
rename it), then rerun the build script above.
