OHA Layout Tools
================

Blender addon for automated creation of layout files from animatics file. Using timeline marker as shot limit guide, it will extract all shots as separate files. Each shot file's name is derived from the marker prefixing it, and its duration from the marker's distance from the next.

Sound (or video, see Preferences) from the animatics will be rendered separately and inserted to its corresponding layout file, so an animator working on a shot only needs to deal with one audio file. It also creates a text file or spreadsheet containing shot list and duration, for render checking purpose.

Pressing SHIFT while clicking "Extract" button will render only the shot prefixed with each selected marker.


Preferences
-----------

- **Export Format**: Choose to export shot list file to ODS spreadsheet, CSV textfile, or none at all.
- **Layout Path**: Sets base path for all extracted sound and .blend files.

  Any occurence of "`%(blendname)`" in this string will be replaced with the .blend file's name. For example, "`../%(blendname)_files`" will create base path `C:/document/test_files` for file `C:/document/blender/test.blend`.
- **Render Video**: If checked, renders .mov (QuickTime) video instead of .wav audio file.
