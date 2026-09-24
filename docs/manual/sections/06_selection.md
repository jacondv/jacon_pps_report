---
id: selection
number: 6
title: Selection & Segments
---
### Drawing a selection

Switch to the **Select** tool and choose a shape in the Selection dock:

- **Polygon** — left-click to add each vertex, then double-click, right-click, or press <kbd>Enter</kbd> to close the shape (needs at least 3 points). <kbd>Backspace</kbd> removes the last point while drawing.
- **Rectangle** — click and drag to define the box.
- **Lasso** — click and drag to freehand-draw the outline.

Hold <kbd>Shift</kbd> while closing the shape to *add* to the current selection, or <kbd>Ctrl</kbd> to *subtract* from it; with neither held, the new shape replaces the current selection.

### Filtering by thickness

The *Filter by Thickness* panel lets you type a thickness range and click **Select by Thickness** to automatically select every point whose value falls inside it — useful for isolating under- or over-sprayed areas without manually drawing a shape.

### Extracting a segment

Once you have a selection, two actions turn it into a new segment (layer):

- **Extract Inside** — creates a new segment from the points *inside* the current selection.
- **Extract Outside** — creates a new segment from the points *outside* the current selection (crop away what's selected).

The other Actions buttons — **Select All**, **Invert**, and **Clear** — operate on the current selection without creating a segment.

A newly extracted segment is shown on its own (every other layer is temporarily hidden) and appears as a new top-level entry in the [Project tree](#project-tree). Notes, Annotations and measurements placed on a segment belong to it and will hide/show together with it.
