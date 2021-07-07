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

import bpy


class OHA_LayoutToolsProperties(bpy.types.PropertyGroup):
    bl_idname = "oha.layout_tools_properties"

    render_marker_infos = []
    marker_infos = []


class OHA_LayoutToolsPreferences(bpy.types.AddonPreferences):
    bl_idname = "oha.layout_tools_preferences"

    is_export_ods: bpy.props.BoolProperty(
        name="Shot List to Spreadsheet",
        description="Write shot list to Open Document spreadsheet (.ods)",
        default=True)

    is_export_csv: bpy.props.BoolProperty(
        name="Shot List to CSV Textfile",
        description="Write shot list to Excel comma-separated values.",
        default=False)

    layout_path: bpy.props.StringProperty(
        name="Base Layout Path",
        description="""Base path for all extracted sound and .blend files.
%(blendname): Name of current .blend file.""",
        default="../%(blendname)")

    is_render_video: bpy.props.BoolProperty(
        name="Render Video",
        description="Render video instead of audio file.",
        default=False)

    def draw(self, context):
        layout = self.layout

        cols = layout.column_flow(columns=2, align=True)

        cols.label(text="Export Format:")
        row = cols.row(align=True)
        row.prop(self, "is_export_ods", text="ODS", toggle=True)
        row.prop(self, "is_export_csv", text="CSV", toggle=True)

        cols.label(text="Layout Path:")
        cols.prop(self, "layout_path", text="")

        row = layout.row()
        row.prop(self, "is_render_video")
