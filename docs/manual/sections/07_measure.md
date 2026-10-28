---
id: measure
number: 7
title: Measuring Distance & Area
---
### Distance

Select the **Distance** tool, click the first point on the cloud, move the mouse to see a live preview line and running distance, then click the second point to finish. The result is attached to the nearest segment and appears in the Project tree.

### Area

Select the **Area** tool and draw a frame on the cloud the same way as a selection shape (polygon, rectangle or lasso). When the frame is closed:

- It **snaps onto the cloud surface you are looking at** — the outline is made of cloud points, so it stays attached to the cloud and rotates/zooms with it.
- Only the points **enclosed by that outline on that surface** are measured. Surfaces hidden behind the region (for example the opposite tunnel wall) are never included, whatever the viewing angle.
- The true surface area (not the flat projected area) of those points is computed using Ball-Pivoting surface reconstruction (BPA) — the same method the PDF report itself uses — and is displayed on the model a few seconds later, once the background calculation finishes.

Draw the frame on the cloud itself: parts of the frame drawn on empty background are ignored, and a frame entirely off the cloud creates no measurement. Area measurements from projects saved with an older version keep their value and label but have no outline.

### Changing a measurement's color and font size

Each Distance and Area measurement has its own color (used for its label and its line/outline) and label font size. With the **Navigate** tool active, right-click the measurement's label and choose **Edit…** — or right-click (or double-click) it in the [Project tree](#project-tree) — then pick a color and font size. The change can be undone with <kbd>Ctrl</kbd>+<kbd>Z</kbd> and is saved in the project file.
