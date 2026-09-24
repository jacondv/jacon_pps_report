---
id: interface
number: 2
title: Interface Tour
---
The main window is built from a menu bar, two toolbars, a central 3D viewport, and four dockable panels:

| Area | Purpose |
| --- | --- |
| **Main toolbar** | Open PLY, Undo/Redo, Calculate, Export PDF |
| **Tool toolbar** | The six interaction tools — Navigate, Select, Distance, Area, Note, Annotation — plus quick view-orientation buttons (Reset, Top, Bottom, Front, Back, Right, Left, Iso) |
| **Project dock** | Tree of segments (layers) with their notes/annotations/measurements nested underneath; visibility, rename, delete, edit and move all happen here |
| **Selection dock** | Region-select shape, thickness filter, and segment extraction/crop actions |
| **Properties dock** | Loaded file information, Target Min/Max thickness, default point size |
| **Results dock** | Calculation output: surface area, volume, thickness statistics, and the below/within/above-target distribution |

Every dock can be dragged to a different edge of the window, floated as its own window, or hidden/shown from the `View` menu. If the layout ever gets into an awkward state, use `View → Reset Layout` to restore the default arrangement.
