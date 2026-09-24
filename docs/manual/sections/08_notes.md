---
id: notes
number: 8
title: Notes & Annotations
---
<p class="subtitle">Text placed directly on the 3D view, exported together with the PDF report</p>

### Creating one

**Note** (<kbd>N</kbd>): click anywhere on the view to type text right on the spot. A Note has no 3D anchor — it stays fixed on screen regardless of how the camera moves, and attaches to whichever segment is currently visible (or the original cloud if no segment is visible) purely for organization in the Project tree.

**Annotation** (<kbd>G</kbd>): click a point on the cloud — one end is pinned to that 3D point (marked with a small colored sphere), the other end is the text label, joined by a leader line. An Annotation tracks the model as the camera orbits, and is attached to whichever segment is spatially closest to the clicked point.

```figure
image: notes_example.png
caption: Example: "Crack detected here" is a screen-fixed **Note**;
  "Min thickness zone" is an **Annotation** anchored to the model with a
  leader line.
```

### Editing, moving, and deleting

Switch to the **Navigate** tool (<kbd>V</kbd>) to work with existing Notes/Annotations:

- Click directly on a Note/Annotation in the 3D view to select it (it highlights in orange), or select it from the Project tree — either way stays in sync with the other.
- Drag it to move the text to a new position; it tracks live under the cursor while dragging.
- Right-click for a context menu with **Edit…** (change the text/color/font size) and **Delete**.
- Press <kbd>Delete</kbd> to remove whichever Note/Annotation/measurement is currently selected.

The same Edit/Move/Delete actions are also available by right-clicking the item directly in the [Project tree](#project-tree).
