---
id: overview
number: 1
title: Overview
---
Jacon PPS Report reads a 3D point cloud (`.ply`) produced by the **Jacon
PPS Scan** system, which scans a tunnel or mine face **before** shotcrete
is sprayed (the *Pre-Scan*, the raw excavated rock surface) and again
**after** spraying (the *Post-Scan*). The PPS Scan system computes the
perpendicular distance between the Post-Scan and Pre-Scan surfaces at
every point and writes that signed thickness value into the `.ply` file.

Jacon PPS Report does **not** perform that Pre-Scan/Post-Scan comparison
itself — its job is post-processing and reporting on data that already
carries per-point thickness. It colors the cloud by thickness, lets you
inspect it interactively in 3D, isolate regions of interest as separate
segments, measure distances and areas, annotate findings directly on the
model, compute summary statistics against a target thickness range, and
produce a PDF report suitable for handing to a client or QA reviewer.

Typical end-to-end workflow:

1. Open the post-processed `.ply` scan file (already carries per-point thickness from the PPS Scan system).
2. Review / adjust the target thickness range (Min / Max).
3. Optionally select and extract one or more segments of interest.
4. Measure distances or areas, and place Notes/Annotations to document findings.
5. Run **Calculate** to get the full statistical breakdown.
6. Export the PDF report (and optionally save the working session as a project file).

```figure
image: overview_main_window.png
caption: The main window: tool toolbar across the top-middle, the
  **Project** and **Selection** docks on the left, **Properties** and
  **Results** on the right, and the 3D viewport in the center with the
  thickness color legend.
```
