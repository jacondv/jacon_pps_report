---
id: open-file
number: 3
title: Opening a PLY File
---
Use `File → Open PLY…` (<kbd>Ctrl</kbd>+<kbd>O</kbd>) or the **Open PLY** button on the main toolbar, and choose a `.ply` file that already contains per-point thickness values computed by the PPS System (the Post-Scan surface compared against the Pre-Scan rough surface — not a CAD design profile).

### Filename & folder convention

If the file lives under a path shaped like `…/Projects/<ProjectName>/<JobNumber>/<JobNumber>#<yyyyMMdd_hhmmss>#<SegmentName>.ply`, the project name, job number, scan timestamp and segment name are parsed automatically and shown in the **Properties** dock, and reused to build the default PDF report filename. If the path doesn't match this convention, the file still loads normally — the project/job fields simply fall back to the folder and file names as-is.

### Default target range

The initial **Target Min/Max** thickness is resolved automatically:

- If a `job_info.json` file sits next to the PLY with a `parameters.target_thickness` and `parameters.tolerance`, the range is set to *target − tolerance* to *target + tolerance*.
- Otherwise it defaults to **40–60 mm**.

You can always adjust Min/Max afterwards in the Properties dock — see [Calculation & Targets](#calculate).
