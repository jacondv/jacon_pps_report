---
id: navigation
number: 5
title: 3D Navigation & Tools
---
### Camera controls

Left-drag to orbit, right-drag or scroll to zoom, middle-drag to pan. The view-orientation buttons on the right side of the tool toolbar (**Reset, Top, Bottom, Front, Back, Right, Left, Iso**) snap the camera to standard viewpoints.

### The six tools

```figure
image: navigation_tool_toolbar.png
caption: Tool toolbar: Navigate, Select, Distance, Area, Note, Annotation.
```

| Tool | Shortcut | What it does |
| --- | --- | --- |
| Navigate | <kbd>V</kbd> / <kbd>1</kbd> | Orbit/pan/zoom the camera; select, drag-move, right-click edit/delete any existing Note, Annotation, or measurement |
| Select | <kbd>S</kbd> / <kbd>2</kbd> | Draw a selection region (Polygon / Rectangle / Lasso) on the cloud, used to extract or crop segments |
| Distance | <kbd>D</kbd> / <kbd>3</kbd> | Measure the straight-line distance between two points on the cloud |
| Area | <kbd>A</kbd> / <kbd>4</kbd> | Draw a region and compute its true surface area |
| Note | <kbd>N</kbd> / <kbd>5</kbd> | Place free-floating 2D text anywhere on the view, with no 3D anchor |
| Annotation | <kbd>G</kbd> / <kbd>6</kbd> | Place text anchored to a specific point on the cloud, connected by a leader line |

<div class="callout">
<strong>Auto-return to Navigate:</strong> as soon as a creation tool finishes its action — a Note/Annotation is placed, a Distance/Area measurement completes, or a segment is extracted/cropped — the active tool switches back to <strong>Navigate</strong> automatically, so you can immediately interact with what you just created without pressing another button.
</div>

Press <kbd>Esc</kbd> at any time to cancel an in-progress action (e.g. a half-drawn polygon); pressing it again while idle returns to Navigate.
