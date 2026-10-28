"""
Build src/pps/ui/help/user_guide.html (and a PDF copy) from the per-section
Markdown files under docs/manual/sections/.

Each section file is plain Markdown with a small frontmatter header:

    ---
    id: overview
    number: 1
    title: Overview
    ---
    Body text in Markdown (headings become <h3>, tables use GFM syntax,
    images use the custom ```figure fenced block below).

To insert a screenshot with a caption, use a fenced block:

    ```figure
    image: overview_main_window.png
    caption: Caption text, **bold** allowed.
    ```

Images referenced there must exist in docs/manual/images/ and are copied
next to the built HTML at src/pps/ui/help/images/ so the app can open the
guide as a plain local file with no embedded/base64 data.

Sections whose frontmatter sets `raw: true` are inserted as literal HTML
(no title wrapper, no Markdown conversion) — used for the safety warning
box and the contact card, which are fixed layouts rather than prose.

The same section content is also rendered through template_pdf.html (a
single-column, print-friendly layout — no sticky sidebar) and converted to
User_Guide.pdf via the wkhtmltopdf binary already vendored for PDF report
export (src/pps/report/packages/wkhtmltox), so the guide can be printed or
shared outside the app too.

Run:
    python docs/manual/build_manual.py
"""
import re
import shutil
import sys
from pathlib import Path

import markdown

MANUAL_DIR = Path(__file__).resolve().parent
SECTIONS_DIR = MANUAL_DIR / "sections"
IMAGES_DIR = MANUAL_DIR / "images"
TEMPLATE_FILE = MANUAL_DIR / "template.html"
PDF_TEMPLATE_FILE = MANUAL_DIR / "template_pdf.html"

REPO_ROOT = MANUAL_DIR.parent.parent
HELP_DIR = REPO_ROOT / "src/pps/ui/help"
OUTPUT_FILE = HELP_DIR / "user_guide.html"
OUTPUT_IMAGES_DIR = HELP_DIR / "images"
OUTPUT_PDF = HELP_DIR / "User_Guide.pdf"
REPO_PDF_COPY = MANUAL_DIR / "User_Guide.pdf"
WKHTMLTOPDF = REPO_ROOT / "src/pps/report/packages/wkhtmltox/bin/wkhtmltopdf.exe"

FIGURE_RE = re.compile(r"```figure\s*\n(.*?)\n```", re.DOTALL)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

MD = markdown.Markdown(extensions=["tables", "sane_lists", "md_in_html"])


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("Section file is missing a --- frontmatter header")
    meta = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    body = text[match.end():]
    return meta, body


def render_figure(block: str) -> str:
    fields = {}
    lines = block.splitlines()
    key = None
    for line in lines:
        m = re.match(r"^(image|caption|style|width):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2)
            fields[key] = value
        elif key:
            fields[key] += "\n" + line
    image = fields["image"].strip()
    if not (IMAGES_DIR / image).is_file():
        raise FileNotFoundError(f"docs/manual/images/{image} not found (referenced by a figure block)")
    caption_html = MD.reset().convert(fields.get("caption", "").strip())
    caption_html = re.sub(r"^<p>|</p>$", "", caption_html.strip())
    style_parts = []
    if fields.get("style") == "flush":
        style_parts.append("margin:0")
    if fields.get("width"):
        width = fields["width"].strip()
        style_parts.append(f"max-width:{width}")
        style_parts.append("margin-left:auto")
        style_parts.append("margin-right:auto")
    style = f' style="{";".join(style_parts)};"' if style_parts else ""
    return (
        f'<figure{style}>\n'
        f'        <img src="images/{image}" alt="">\n'
        f'        <figcaption>\n'
        f'          {caption_html}\n'
        f'        </figcaption>\n'
        f'      </figure>'
    )


def render_section(meta: dict, body: str) -> str:
    if meta.get("raw") == "true":
        html_body = body.strip()
    else:
        # Pull out figure blocks so the fenced-code extension doesn't see them.
        figures = []

        def stash_figure(m: re.Match) -> str:
            figures.append(render_figure(m.group(1)))
            return f"@@FIGURE{len(figures) - 1}@@"

        stashed = FIGURE_RE.sub(stash_figure, body)
        html_body = MD.reset().convert(stashed)
        for i, fig_html in enumerate(figures):
            html_body = html_body.replace(f"<p>@@FIGURE{i}@@</p>", fig_html).replace(f"@@FIGURE{i}@@", fig_html)

    if meta.get("title"):
        if meta.get("number"):
            heading = f'<h2><span class="num">{meta["number"]}</span> {meta["title"]}</h2>\n      '
        else:
            heading = f'<h2>{meta["title"]}</h2>\n      '
    else:
        heading = ""

    indented_body = "\n".join(
        ("      " + line) if line.strip() else "" for line in html_body.splitlines()
    )
    return f'    <section id="{meta["id"]}">\n      {heading}{indented_body.strip()}\n    </section>\n'


def render_pdf(toc_html: str, sections_html: str) -> None:
    if not WKHTMLTOPDF.is_file():
        print(f"Skipping PDF: wkhtmltopdf not found at {WKHTMLTOPDF}", file=sys.stderr)
        return

    import pdfkit

    pdf_template = PDF_TEMPLATE_FILE.read_text(encoding="utf-8")
    pdf_html = pdf_template.replace("{{TOC}}", toc_html).replace("{{SECTIONS}}", sections_html)

    # Written next to OUTPUT_IMAGES_DIR (already populated by main()) so the
    # figure blocks' relative "images/…" src resolves the same as the HTML.
    source_file = HELP_DIR / "_user_guide_pdf_source.html"
    source_file.write_text(pdf_html, encoding="utf-8", newline="\n")

    config = pdfkit.configuration(wkhtmltopdf=str(WKHTMLTOPDF))
    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "margin-top": "15mm",
        "margin-bottom": "15mm",
        "margin-left": "18mm",
        "margin-right": "18mm",
    }
    try:
        pdfkit.from_file(str(source_file), str(OUTPUT_PDF), options=options, configuration=config)
    finally:
        source_file.unlink(missing_ok=True)

    shutil.copyfile(OUTPUT_PDF, REPO_PDF_COPY)
    print(f"Wrote {OUTPUT_PDF} (and a copy at {REPO_PDF_COPY})")


def main() -> None:
    section_files = sorted(SECTIONS_DIR.glob("*.md"))
    if not section_files:
        raise SystemExit("No section files found under docs/manual/sections/")

    toc_lines = []
    section_html = []
    for path in section_files:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        section_html.append(render_section(meta, body))
        nav_label = meta.get("nav") or (
            f'{meta["number"]}. {meta["title"]}' if meta.get("number") else meta.get("title", meta["id"])
        )
        toc_lines.append(f'    <a href="#{meta["id"]}">{nav_label}</a>')

    toc_html = "\n".join(toc_lines)
    sections_html = "\n".join(section_html)

    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    html = template.replace("{{TOC}}", toc_html).replace("{{SECTIONS}}", sections_html)

    HELP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8", newline="\n")

    if OUTPUT_IMAGES_DIR.exists():
        shutil.rmtree(OUTPUT_IMAGES_DIR)
    shutil.copytree(IMAGES_DIR, OUTPUT_IMAGES_DIR)

    print(f"Wrote {OUTPUT_FILE} ({len(section_files)} sections, {len(list(OUTPUT_IMAGES_DIR.iterdir()))} images)")

    render_pdf(toc_html, sections_html)


if __name__ == "__main__":
    main()
