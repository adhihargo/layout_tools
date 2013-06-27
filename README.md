OHA Layout Tools
================

Blender addon for automated creation of layout files from animatics file. Using timeline marker as shot limit guide, it will extract all shots as separate files. Each shot file's name is derived from the marker prefixing it, and its duration from the marker's distance from the next.

Sound from the animatics will be rendered separately and inserted to its corresponding layout file, so an animator working on a shot only needs to deal with one audio file. It also creates a text file containing shot list and duration, for render checking purpose.

Pressing SHIFT while clicking "Extract" button will render only the shot prefixed with each selected marker.
