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
import threading

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
    render_count = 0

class SEQUENCER_OT_ExtractShotfiles(bpy.types.Operator):
    '''Automatically create layout files using marker boundaries.'''
    bl_idname = 'sequencer.oha_extract_shotfiles'
    bl_label = 'Create Layout'
    bl_options = {'REGISTER'}

    blendpath = None            # path of .blend file to restore back to
    basepath = None             # base path of layout files
    render_selected = False
    marker_infos = []
    render_marker_infos = []

    _timer = None
    _render_thread = None

    @classmethod
    def poll(self, context):
        # The operator needs the scene to be already saved in a file,
        # and there's no unrendered shot marker.
        return context.blend_data.is_saved\
            and not self.render_marker_infos

    def write_listing(self, lpath):
        # Write the duration of each shots (difference of adjacent
        # markers) to a text file.
        lfile = open(lpath, 'w')
        for mi in self.marker_infos:
            lfile.write("%s:\t%s frames.\n" % (mi['name'],
                                               mi['end'] - mi['start']))
        lfile.close()

    def _init_render_thread(self):
        self._render_thread = threading.Thread(
            target=bpy.ops.render.render, kwargs={'animation':True})

    def _init_marker_infos(self, context):
        # Store marker informations so the markers themselves can be
        # deleted.
        scene = context.scene
        props = scene.oha_layout_tools

        markers = [marker for marker in scene.timeline_markers
                   if marker.frame >= scene.frame_start
                   and marker.frame < scene.frame_end]
        markers.sort(key=lambda m: m.frame)

        self.marker_infos.clear()
        for m, frame_end in zip(
            markers, [m.frame for m in markers[1:]]+[scene.frame_end]):
            self.marker_infos.append({'name':m.name,
                                      'select':m.select,
                                      'start':m.frame,
                                      'end':frame_end})

        self.render_marker_infos.clear()
        self.render_marker_infos.extend(
            [mi for mi in self.marker_infos if mi['select'] == True]
            if self.render_selected else self.marker_infos)
        props.render_count = len(self.render_marker_infos)
        
    def adjust_duration_to_effects(self, context):
        scene = context.scene
        sequences = scene.sequence_editor.sequences

        effects = [seq for seq in sequences
                   if isinstance(seq, bpy.types.EffectSequence)
                   and seq.type not in ['COLOR',
                                        'MULTICAM',
                                        'ADJUSTMENT']]
        for mi in self.marker_infos:
            overlap_start = [e for e in effects
                             if mi['start'] == e.frame_final_end]
            overlap_end = [e for e in effects
                           if mi['end'] == e.frame_final_start]
            if overlap_start:
                mi['start'] = overlap_start[0].frame_final_start
            if overlap_end:
                mi['end'] = overlap_end[0].frame_final_end

    def marker_scene_settings(self, context, mi):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg

        scene.frame_start =  mi['start']
        scene.frame_end = mi['end']

        render.filepath = os.path.join(self.basepath, 'sounds',
                                       mi['name']+'.wav')
        render.image_settings.file_format = 'H264'

        ffmpeg.format = 'WAV'
        ffmpeg.audio_codec = 'PCM'
        ffmpeg.audio_bitrate = 192

    def _check_render_thread(self, context):
        scene = context.scene
        props = scene.oha_layout_tools
        scene.timeline_markers.clear()
        sequences = scene.sequence_editor.sequences

        if self._render_thread.is_alive():
            return {'PASS_THROUGH'}
        else:
            self._init_render_thread()

        if self.render_marker_infos:
            rmi = self.render_marker_infos.pop(0)
            # context.window_manager.progress_update(
            #     props.render_count - len(self.render_marker_infos))
            self.marker_scene_settings(context, rmi)
            context.screen.update_tag()

            self._render_thread.start()

            return {'PASS_THROUGH'}

        bpy.ops.sequencer.select_all(action='SELECT')
        bpy.ops.sequencer.delete()
        for mi in self.marker_infos:
            duration = mi['end'] - mi['start']
            scene.frame_end = scene.frame_start + duration

            soundpath = os.path.join(self.basepath, 'sounds',
                                     mi['name']+'.wav')
            if os.path.isfile(soundpath):
                seq = sequences.new_sound(mi['name'], soundpath,
                                          1, scene.frame_start)

            layoutdir = os.path.join(self.basepath, 'layouts')
            markerpath = bpy.path.ensure_ext(
                filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
            bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                        relative_remap=True)
            sequences.remove(seq)

        bpy.ops.wm.open_mainfile(filepath=self.blendpath)

        return {'FINISHED'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        
        return {'CANCELLED'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            return self._check_render_thread(context)
        elif event.type == 'ESC':
            self.marker_infos.clear()
            self.render_marker_infos.clear()

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        props = scene.oha_layout_tools

        self.blendpath = bpy.path.abspath(context.blend_data.filepath)

        self._init_marker_infos(context)
        if not self.marker_infos:
            return self.cancel(context)
        self.adjust_duration_to_effects(context)
        
        blenddir, blendfile = os.path.split(self.blendpath)
        blenddir0, blenddir1 = os.path.split(blenddir)
        blendfile_base = os.path.splitext(blendfile)[0]
        if blenddir1:
            self.basepath = os.path.join(blenddir0, blendfile_base)
            layoutdir = os.path.join(self.basepath, 'layouts')
            if not os.path.exists(layoutdir):
                os.makedirs(layoutdir)

        self.write_listing(os.path.join(blenddir, blendfile_base + '.txt'))

        wm.modal_handler_add(self)
        self._timer = wm.event_timer_add(1.0, context.window)
        self._init_render_thread()
        # context.window_manager.progress_begin(0, props.render_count)

        return {'RUNNING_MODAL'}

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
    
