---
id: projects
number: 4
title: Saving & Opening Projects
---
Besides the source `.ply`, the application can save your entire working session — segments, notes, annotations, measurements, target range, camera position — to a `.ppsproj` project file, so you can close the app and pick up exactly where you left off.

| Action | Shortcut | Notes |
| --- | --- | --- |
| Save Project | <kbd>Ctrl</kbd>+<kbd>S</kbd> | Saves to the current project path; behaves like Save As on the first save |
| Save Project As… | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>S</kbd> | Always prompts for a location |
| Open Project… | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>O</kbd> | Loads a `.ppsproj` file |
| Recent Projects | — | Submenu under `File` listing recently opened projects |

<div class="callout">
<strong>Unsaved changes:</strong> opening another file/project, or closing the app, while there are unsaved changes prompts you to Save, Discard, or Cancel — nothing is lost silently.
</div>

Once a project has been saved, exporting a PDF report from it works immediately without needing to reload the original `.ply` file.
