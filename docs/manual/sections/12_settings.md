---
id: settings
number: 12
title: Application Settings
---
<div class="grid-2" markdown="1">
<div markdown="1">

Open `Settings → Preferences…` to configure theme, point size, thickness classification colors, 3D view background, report title/logo, and PDF auto-open. These preferences are stored per-user and persist across sessions and across different point cloud files.

</div>

```figure
image: settings_dialog.png
caption: The Settings dialog, including the PDF Export auto-open option.
style: flush
```

</div>

| Setting | Effect |
| --- | --- |
| Theme | Light or Dark UI appearance |
| Point size | Rendered point size. Also adjustable in the Properties dock; the last size used is remembered for the next launch, and opening a project applies the size saved in it |
| Thickness Classification Colors | The three colors used for Below / Within / Above target |
| 3D View Background | Viewport background color — independent of Theme, since it is baked into the PDF report's screenshot |
| Report title | The heading printed at the top of the PDF report (default: "SHOTCRETE THICKNESS REPORT") |
| Report logo | Custom logo image (PNG/JPG/SVG) printed on the report; **Reset** reverts to the default Jacon logo |
| Automatically open the report after exporting | Whether Export PDF opens the resulting file automatically (see above) |
