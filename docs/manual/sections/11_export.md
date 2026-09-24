---
id: export
number: 11
title: Exporting PDF Reports
---
Once **Calculate** has run, click **Export PDF…** (<kbd>Ctrl</kbd>+<kbd>E</kbd>) on the toolbar and choose where to save. The default filename is built from the parsed project name, job number, scan time and segment name (see [Opening a PLY File](#open-file)).

The generated report includes:

- A snapshot of the current 3D view (including any visible Notes/Annotations and the color legend).
- The full Calculate results table and thickness distribution.
- Project/job information parsed from the filename.
- The set of segments that were visible at export time.

<div class="callout">
<strong>Automatically opening the report:</strong> go to <code>Settings &rarr; Preferences&hellip;</code>, section <em>PDF Export</em>, and toggle <strong>"Automatically open the report after exporting"</strong>. When enabled (the default), the PDF opens in your system's default PDF viewer immediately after export completes — no confirmation dialog is shown either way.
</div>

<div class="callout">
<strong>Customizing the report title and logo:</strong> go to <code>Settings &rarr; Preferences&hellip;</code>, section <em>Report</em>. Change <strong>Report title</strong> to replace the heading printed at the top of every exported PDF, and use <strong>Report logo &rarr; Browse&hellip;</strong> to pick your own image (PNG/JPG/SVG) instead of the default Jacon logo — click <strong>Reset</strong> to go back to the default. Both settings are saved per-user and apply to every report exported afterwards.
</div>
