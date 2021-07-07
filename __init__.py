# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This file is part of OHA Layout Tools.
#
#  OHA Layout Tools is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  OHA Layout Tools is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with OHA Layout Tools.  If not, see <https://www.gnu.org/licenses/>.
#
#
# ##### END GPL LICENSE BLOCK #####

# Author: Adhi Hargo (cadmus.sw@gmail.com)

if "bpy" in locals():
    import importlib

    importlib.reload(app)
    importlib.reload(constants)
    importlib.reload(data)
    importlib.reload(ui)
else:
    from . import app, constants, data, ui

import bpy

bl_info = {
    "name": "OHA Layout Tools",
    "author": "Adhi Hargo, Johan Tri Handoyo",
    "version": (1, 0, 4),
    "blender": (2, 92, 0),
    "location": "Sequencer > Tools > OHA Layout Tools",
    "description": "Create layout files.",
    "warning": "",
    "wiki_url": "https://github.com/johantri/layout_tools",
    "tracker_url": "https://github.com/johantri/layout_tools/issues",
    "category": "Sequencer"}

classes = [data.OHA_LayoutToolsProperties, data.OHA_LayoutToolsPreferences, app.SEQUENCER_OT_ExtractShotfiles,
           app.SCENE_OT_RenameMarkers, app.SCENE_OT_ImportAssets, app.OBJECT_OT_ProxyMakeAll, ui.VIEW3D_PT_ProxyMakeAll]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    ui.register()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    ui.unregister()


if __name__ == "__main__":
    register()
