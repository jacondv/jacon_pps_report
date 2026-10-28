---
id: project-tree
number: 9
title: The Project Tree
---
<div class="grid-2" markdown="1">
<div markdown="1">

The **Project** dock on the left shows every segment (layer) as a top-level row, with its Notes, Annotations and measurements nested underneath as child rows. Toggling a segment's checkbox hides or shows everything nested inside it in one action.

Selecting multiple rows (<kbd>Ctrl</kbd>/<kbd>Shift</kbd>-click) enables a bulk **Delete** action, applied as a single undo step. Notes/measurements with no owning segment (for example, after their segment was deleted) are grouped under an **(Unassigned)** entry rather than being lost.

</div>

```figure
image: project_tree.png
caption: Project tree, checkboxes control visibility; right-click a
  segment to Rename/Delete, or an object to Edit/Move/Hide/Delete.
style: flush
```

</div>

| Row type | Right-click menu |
| --- | --- |
| Segment (layer) | Rename…, Delete layer (not available for the original cloud) |
| Note / Annotation | Edit…, Move, Hide/Show, Delete |
| Distance / Area measurement | Edit… (color and font size), Hide/Show, Delete — double-click also opens Edit… |
