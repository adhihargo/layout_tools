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

from . import app, data


class VIEW3D_PT_ProxyMakeAll(bpy.types.Panel):
    # Create proxy from any selected linked objects
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "OHA"
    bl_context = "objectmode"
    bl_label = "OHA Make Proxies"

    def draw(self, context):
        layout = self.layout
        layout.operator(app.OBJECT_OT_ProxyMakeAll.bl_idname, icon="LINK_BLEND")


def menu_func_import(self, context):
    self.layout.operator(app.SCENE_OT_ImportAssets.bl_idname)


def draw_func(self, context):
    layout = self.layout
    if context.space_data.view_type == 'SEQUENCER':
        layout.operator(app.SCENE_OT_RenameMarkers.bl_idname, icon='LINENUMBERS_ON')


def sequencer_headerbutton(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.operator(app.SEQUENCER_OT_ExtractShotfiles.bl_idname, icon='DOCUMENTS', text='Extract')


def register():
    if bpy.app.version < (2, 80):
        bpy.types.INFO_MT_file_import.append(menu_func_import)
    else:
        bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.types.Scene.oha_layout_tools = bpy.props.PointerProperty(type=data.OHA_LayoutToolsProperties)
    bpy.types.SEQUENCER_HT_header.append(sequencer_headerbutton)
    bpy.types.SEQUENCER_HT_header.append(draw_func)


def unregister():
    if bpy.app.version < (2, 80):
        bpy.types.INFO_MT_file_import.remove(menu_func_import)
    else:
        bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    del bpy.types.Scene.oha_layout_tools
    bpy.types.SEQUENCER_HT_header.remove(sequencer_headerbutton)
    bpy.types.SEQUENCER_HT_header.remove(draw_func)
