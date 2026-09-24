---
id: undo
number: 13
title: Undo, Redo & Safety
---
Nearly every change — selections turned into segments, renames, deletes, target range edits, moving/editing a Note or Annotation — is recorded on a single undo stack, so <kbd>Ctrl</kbd>+<kbd>Z</kbd> / <kbd>Ctrl</kbd>+<kbd>Y</kbd> (Undo/Redo) works consistently across the whole application. Bulk operations (deleting multiple selected rows in the Project tree, for example) are grouped into a single undo step.

The window title and the Save Project action reflect whether there are unsaved changes; closing the app or opening another file/project while changes are pending will always ask whether to save first.
