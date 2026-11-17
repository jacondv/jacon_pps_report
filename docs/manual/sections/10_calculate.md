---
id: calculate
number: 10
title: Calculation & Targets
---
<div class="grid-2" markdown="1">
<div markdown="1">

In the **Properties** dock, set **Min target thickness** and **Max target thickness** (mm) to match the design requirement. The model re-colors automatically about 0.5 seconds after you stop typing. Max is always kept ≥ Min automatically.

Click **Calculate** on the main toolbar to run the full analysis of the **visible** clouds. This runs in the background so the UI stays responsive on large clouds.

The results belong to the targets and visible clouds they were calculated for. Changing either — editing Min/Max, or showing/hiding a cloud in the Project tree — clears the Results dock; click **Calculate** again (renaming or recoloring a cloud does not).

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
| Below / Within / Above Target | Point counts and percentages split by the Target Min/Max range (out-of-range points not included) |
| Out of Range | Points thicker than the max measurable thickness (default 300 mm), treated as noise |

The color classes correspond to the colors configured in [Settings](#settings):

- **Below Target Min** (default: red) — insufficient shotcrete thickness.
- **Within Target Min–Max** (default: green) — meets the design requirement.
- **Above Target Max** (default: blue) — over-sprayed beyond the target.
- **Above Max Measurable** (default: light blue) — outside the PPS System's measurable range, treated as noise.

<div class="callout warn">
<strong>Note:</strong> thickness is taken as an absolute value, and values below 12 mm are treated as no measurable deviation (0 mm). Values above the <strong>max measurable thickness</strong> (default 300 mm, the PPS System hardware's valid measurement range; change it in <a href="#settings">Settings</a>) are treated as scan noise: they are left out of the thickness statistics, the target coverage, the volume and the distribution chart, but still count towards the total surface area so the surface has no holes. When there are such points, the report prints a warning under the distribution chart with their number and share — a high share usually means the pre-scan and post-scan are misaligned.
</div>
