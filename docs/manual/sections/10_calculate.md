---
id: calculate
number: 10
title: Calculation & Targets
---
<div class="grid-2" markdown="1">
<div markdown="1">

In the **Properties** dock, set **Min target thickness** and **Max target thickness** (mm) to match the design requirement. The model re-colors and the Results dock refreshes automatically about 0.5 seconds after you stop typing. Max is always kept ≥ Min automatically.

Click **Calculate** on the main toolbar to run the full analysis. This runs in the background so the UI stays responsive on large clouds.

</div>

```figure
image: calculate_properties_dock.png
caption: Properties dock, file info, Target Min/Max, point size.
style: flush
```

</div>

### Reading the Results

| Field | Meaning |
| --- | --- |
| Surface Area (m²) | Total reconstructed surface area of the visible cloud |
| Target Coverage (m²) | Surface area of the region that reached the minimum target thickness |
| Volume (m³) | Target-coverage area × mean thickness of that region |
| Mean / Min / Max Thickness (mm) | Statistics computed over points that reached the target thickness |
| Std Deviation | Standard deviation of thickness over the same set of points |
| Number of Points | Total point count in the visible cloud |
| Below / Within / Above Target | Point counts and percentages split by the Target Min/Max range |

The three color classes correspond to the colors configured in [Settings](#settings):

- **Below Target Min** (default: red) — insufficient shotcrete thickness.
- **Within Target Min–Max** (default: green) — meets the design requirement.
- **Above Target Max** (default: blue) — over-sprayed beyond the target.

<div class="callout warn">
<strong>Note:</strong> thickness values with an absolute magnitude below 12 mm are treated as no measurable deviation, and values above 500 mm are treated as scan noise — both are excluded from the "reached target" statistics. The PPS Scan hardware's own valid measurement range is 0–300 mm, so the 500 mm cutoff is a deliberately generous software-side margin above that — it only catches genuine scan artifacts (e.g. reflections), not real thickness readings.
</div>
