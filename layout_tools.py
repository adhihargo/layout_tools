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

    basepath = None
    render_selected = False

    @classmethod
    def poll(self, context):
        # The operator needs the scene to be already saved in a file.
        return context.blend_data.is_saved

    def write_listing(self, marker_infos, lpath):
        # Write the duration of each shots (difference of adjacent
        # markers) to a text file.
        lfile = open(lpath, 'w')
        for mi in marker_infos:
            lfile.write("%s:\t%s frames.\n" % (mi['name'],
                                               mi['end'] - mi['start']))
        lfile.close()

    def create_marker_infos(self, context):
        # Store marker informations so the markers themselves can be
        # deleted.
        scene = context.scene

        markers = [marker for marker in scene.timeline_markers
                   if marker.frame >= scene.frame_start
                   and marker.frame < scene.frame_end]
        markers.sort(key=lambda m: m.frame)

        marker_infos = []
        for m, frame_end in zip(
            markers, [m.frame for m in markers[1:]]+[scene.frame_end]):
            marker_infos.append({'name':m.name,
                                 'select':m.select,
                                 'start':m.frame,
                                 'end':frame_end})

        return marker_infos

    def save_marker_delimited_file(self, context, layoutdir, mi):
        markerpath = bpy.path.ensure_ext(
            filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
        bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                    relative_remap=True)

    def modify_scene_settings(self, context, mi):
        scene = context.scene
        render = scene.render
        ffmpeg = render.ffmpeg

        duration = mi['end'] - mi['start']
        scene.frame_end = scene.frame_start + duration
        render.filepath = os.path.join(self.basepath, 'sounds',
                                       mi['name']+'.wav')
        render.image_settings.file_format = 'H264'
        ffmpeg.format = 'WAV'
        ffmpeg.audio_codec = 'PCM'
        ffmpeg.audio_bitrate = 192

    def execute(self, context):
        scene = context.scene
        blendpath = bpy.path.abspath(context.blend_data.filepath)

        blenddir, blendfile = os.path.split(blendpath)
        blenddir0, blenddir1 = os.path.split(blenddir)
        blendfile_base = os.path.splitext(blendfile)[0]
        if blenddir1:
            self.basepath = os.path.join(blenddir0, blendfile_base)
            layoutdir = os.path.join(self.basepath, 'layouts')
            if not os.path.exists(layoutdir):
                os.makedirs(layoutdir)

        marker_infos = self.create_marker_infos(context)
        if not marker_infos:
            return {'CANCELLED'}
        
        scene.timeline_markers.clear()
        self.write_listing(marker_infos,
                           os.path.join(blenddir, blendfile_base + '.txt'))

        scene.sequence_editor.show_overlay = True
        scene.frame_current = scene.frame_start
        sequences = scene.sequence_editor.sequences
        prev_offset = 0
        for mi in marker_infos:
            offset = mi['start'] - (scene.frame_start + prev_offset)

            # Most effect strip's frame range depends on at least one
            # other strip (except Color, MultiCam and Adjustment), so
            # musn't be manipulated directly.
            sequences_sorted = sorted([seq for seq in sequences
                                       if not (isinstance(seq, bpy.types.EffectSequence)
                                               and seq.type not in ['COLOR',
                                                                    'MULTICAM',
                                                                    'ADJUSTMENT'])],
                                      key=lambda s: s.frame_final_start)

            # delete_seq_pre = [
            #     seq for seq in sequences_sorted
            #     if seq.frame_final_end - offset < scene.frame_start]
            # delete_seq_post = [
            #     seq for seq in sequences_sorted
            #     if seq.frame_start - offset >= scene.frame_end]

            for seq in sequences_sorted:
                seq.frame_start -= offset
                seq.select = False
            prev_offset += offset

            # bpy.ops.sequencer.delete({'selected_sequences': delete_seq_post,
            #                           'window': context.window,
            #                           'scene': context.scene},
            #                          'INVOKE_DEFAULT', True)
            self.modify_scene_settings(context, mi)
            if self.render_selected and mi['select']:
                bpy.ops.render.render(animation=True)
            self.save_marker_delimited_file(context, layoutdir, mi)
            # bpy.ops.ed.undo('INVOKE_DEFAULT')

        bpy.ops.wm.open_mainfile(filepath=blendpath)

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.shift: self.render_selected = True
        return self.execute(context)

def sequencer_headerbutton(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.operator('sequencer.oha_extract_shotfiles', icon='ALIGN', text='Extract')

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.oha_layout_tools = bpy.props.PointerProperty(
        type = OHA_LayoutToolsProps)
    bpy.types.SEQUENCER_HT_header.append(sequencer_headerbutton)

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.oha_layout_tools
    bpy.types.SEQUENCER_HT_header.remove(sequencer_headerbutton)
    
