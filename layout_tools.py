# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Author: Adhi Hargo (cadmus.sw@gmail.com)

import bpy
import os

bl_info = {
    "name": "OHA Layout Tools",
    "author": "Adhi Hargo",
    "version": (1, 0, 0),
    "blender": (2, 67, 0),
    "location": "Sequencer > Tools > OHA Layout Tools",
    "description": "Create layout files.",
    "warning": "",
    "wiki_url": "https://github.com/adhihargo/layout_tools",
    "tracker_url": "https://github.com/adhihargo/layout_tools/issues",
    "category": "Sequencer"}

class OHA_LayoutToolsProps(bpy.types.PropertyGroup):
    pass

class SEQUENCER_OT_ExtractShotfiles(bpy.types.Operator):
    '''Automatically create layout files using marker boundaries.'''
    bl_idname = 'sequencer.oha_extract_shotfiles'
    bl_label = 'Create Layout'
    bl_options = {'REGISTER'}

    def write_listing(self, marker_infos, lpath):
        lfile = open(lpath, 'w')
        for mi in marker_infos:
            lfile.write("%s:\t%s frames.\n" % (mi['name'], mi['end'] - mi['start']))
        lfile.close()

    def create_marker_infos(self, context):
        scene = context.scene

        markers = [marker for marker in scene.timeline_markers
                   if marker.frame >= scene.frame_start
                   and marker.frame < scene.frame_end]
        markers.sort(key=lambda m: m.frame)

        marker_infos = []
        for m, frame_end in zip(markers,
                                [m.frame for m in markers[1:]]+[scene.frame_end]):
            marker_infos.append({'name':m.name,
                                 'start':m.frame,
                                 'end':frame_end})

        return marker_infos

    def save_marker_delimited_file(self, context, layoutdir, mi):
        markerpath = bpy.path.ensure_ext(
            filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
        bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                    relative_remap=True)

    def execute(self, context):
        scene = context.scene
        blendpath = bpy.path.abspath(context.blend_data.filepath)

        blenddir, blendfile = os.path.split(blendpath)
        blenddir0, blenddir1 = os.path.split(blenddir)
        blendfile_base = os.path.splitext(blendfile)[0]
        if blenddir1:
            layoutdir = os.path.join(blenddir0, blendfile_base,
                                     'layouts')
            if not os.path.exists(layoutdir):
                os.makedirs(layoutdir)
        marker_infos = self.create_marker_infos(context)

        if not marker_infos:
            return {'CANCELLED'}
        
        scene.timeline_markers.clear()
        self.write_listing(marker_infos, os.path.join(blenddir, blendfile_base + '.txt'))

        scene.sequence_editor.show_overlay = True
        sequences = scene.sequence_editor.sequences
        prev_offset = 0
        for mi in marker_infos:
            scene.frame_current = scene.frame_start
            duration = mi['end'] - mi['start']
            offset = mi['start'] - scene.frame_start - prev_offset
            sequences_sorted = list(sequences)
            sequences_sorted.sort(key=lambda s: s.frame_final_start)
            for seq in list(sequences_sorted):
                if seq.frame_final_end - offset <= scene.frame_start:
                    sequences.remove(seq)
                else:
                    seq.frame_final_start -= offset
                    seq.frame_final_end -= offset
            prev_offset = offset
            scene.frame_end = scene.frame_start + duration

            # deletion = 0
            # for seq in list(sequences):
            #     if seq.frame_final_start >= scene.frame_end:
            #         print("Removing %s" % seq.name)
            #         sequences.remove(seq)
            #         deletion += 1
            self.save_marker_delimited_file(context, layoutdir, mi)
            # print("Undoing %d deletion" % deletion)
            # for i in range(deletion):
            #     bpy.ops.ed.undo('INVOKE_DEFAULT')

        bpy.ops.wm.open_mainfile(filepath=blendpath)

        return {'FINISHED'}

def sequencer_headerbutton(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.operator('sequencer.oha_extract_shotfiles', icon='ALIGN', text='Extract')

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.oha_layout_tools = bpy.props.PointerProperty(type = OHA_LayoutToolsProps)
    bpy.types.SEQUENCER_HT_header.append(sequencer_headerbutton)

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.oha_layout_tools
    bpy.types.SEQUENCER_HT_header.remove(sequencer_headerbutton)
    
