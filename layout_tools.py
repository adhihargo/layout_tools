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
from bpy.app.handlers import persistent

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

RS_INIT = 0
RS_RUNNING = 1
RS_FINISHED = 2

class OHA_LayoutToolsProps(bpy.types.PropertyGroup):
    render_count = 0
    render_state = RS_INIT
    render_marker_infos = []
    render_selected = False
    marker_infos = []
    render_basepath = ''

    scene_frame_start = None
    scene_frame_end = None

    render_filepath = None
    image_file_format = None

    ffmpeg_format = None
    ffmpeg_audio_codec = None
    ffmpeg_audio_bitrate = None


# ============================== operators =============================

class SEQUENCER_OT_ExtractShotfiles(bpy.types.Operator):
    '''Automatically create layout files using marker boundaries.'''
    bl_idname = 'sequencer.oha_extract_shot_files'
    bl_label = 'Create Layout'
    bl_options = {'REGISTER'}

    blendpath = None            # path of .blend file to restore back to
    basepath = None             # base path of layout files
    marker_infos = []
    render_marker_infos = []

    # _timer = None

    @classmethod
    def poll(self, context):
        props = context.scene.oha_layout_tools

        # The operator needs the scene to be already saved in a file,
        # and there's no unrendered shot marker.
        return context.blend_data.is_saved\
            and not props.render_marker_infos

    def _init_marker_infos(self, context):
        # Store marker informations so the markers themselves can be
        # deleted.
        scene = context.scene
        props = scene.oha_layout_tools

        markers = [marker for marker in scene.timeline_markers
                   if marker.frame >= scene.frame_start
                   and marker.frame < scene.frame_end]
        markers.sort(key=lambda m: m.frame)

        props.marker_infos.clear()
        for m, frame_end in zip(
            markers, [m.frame for m in markers[1:]]+[scene.frame_end]):
            props.marker_infos.append({'name':m.name,
                                      'select':m.select,
                                      'start':m.frame,
                                      'end':frame_end})

        props.render_marker_infos.clear()
        props.render_marker_infos.extend(
            [mi for mi in props.marker_infos if mi['select'] == True]
            if props.render_selected else props.marker_infos)
        props.render_count = len(props.render_marker_infos)
        
    def _check_render_progress(self, context):
        bpy.ops.wm.open_mainfile(filepath=self.blendpath)

        return {'FINISHED'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            return self._check_render_progress(context)
        elif event.type == 'ESC':
            if render_complete_handler in bpy.app.handlers.render_complete:
                bpy.app.handlers.render_complete.remove(render_complete_handler)

        return {'PASS_THROUGH'}

    def execute(self, context):
        scene = context.scene
        props = scene.oha_layout_tools

        self.blendpath = bpy.path.abspath(context.blend_data.filepath)

        self._init_marker_infos(context)
        if not props.marker_infos:
            return self.cancel(context)
        adjust_duration_to_effects(context)
        
        blenddir, blendfile = os.path.split(self.blendpath)
        blenddir0, blenddir1 = os.path.split(blenddir)
        blendfile_base = os.path.splitext(blendfile)[0]
        if blenddir1:
            props.render_basepath = os.path.join(blenddir0, blendfile_base)
            layoutdir = os.path.join(props.render_basepath, 'layouts')
            if not os.path.exists(layoutdir):
                os.makedirs(layoutdir)

        write_shot_listing(context,
                           os.path.join(blenddir, blendfile_base + '.txt'))
        save_scene_settings(context)

        bpy.app.handlers.render_pre.append(render_pre_handler)
        bpy.app.handlers.render_complete.append(render_complete_handler)

        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

        return {'FINISHED'}

    def invoke(self, context, event):
        props = context.scene.oha_layout_tools
        if event.shift: props.render_selected = True

        return self.execute(context)


# ========================= auxiliary functions ========================

def write_shot_listing(context, lpath):
    props = context.scene.oha_layout_tools

    # Write the duration of each shots (difference of adjacent
    # markers) to a text file.
    lfile = open(lpath, 'w')
    for mi in props.marker_infos:
        lfile.write("%s:\t%s frames.\n" % (mi['name'],
                                           mi['end'] - mi['start']))
    lfile.close()

def write_shot_files(context):
    scene = context.scene
    props = scene.oha_layout_tools
    scene.timeline_markers.clear()
    sequences = scene.sequence_editor.sequences

    restore_scene_settings(context)
    bpy.ops.sequencer.select_all(action='SELECT')
    bpy.ops.sequencer.delete()
    for mi in props.marker_infos:
        duration = mi['end'] - mi['start']
        scene.frame_end = scene.frame_start + duration

        soundpath = os.path.join(props.render_basepath, 'sounds',
                                 mi['name']+'.wav')
        if os.path.isfile(soundpath):
            seq = sequences.new_sound(mi['name'], soundpath,
                                      1, scene.frame_start)

        layoutdir = os.path.join(props.render_basepath, 'layouts')
        markerpath = bpy.path.ensure_ext(
            filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
        bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                    relative_remap=True)
        sequences.remove(seq)
    
def adjust_duration_to_effects(context):
    scene = context.scene
    props = scene.oha_layout_tools
    sequences = scene.sequence_editor.sequences

    effects = [seq for seq in sequences
               if isinstance(seq, bpy.types.EffectSequence)
               and seq.type not in ['COLOR',
                                    'MULTICAM',
                                    'ADJUSTMENT']]
    for mi in props.marker_infos:
        overlap_start = [e for e in effects
                         if mi['start'] == e.frame_final_end]
        overlap_end = [e for e in effects
                       if mi['end'] == e.frame_final_start]
        if overlap_start:
            mi['start'] = overlap_start[0].frame_final_start
        if overlap_end:
            mi['end'] = overlap_end[0].frame_final_end

def marker_scene_settings(context, mi):
    scene = context.scene
    render = scene.render
    image = render.image_settings
    ffmpeg = render.ffmpeg

    scene.frame_start =  mi['start']
    scene.frame_end = mi['end']

    render.filepath = os.path.join(props.render_basepath, 'sounds',
                                   mi['name']+'.wav')
    render.image_settings.file_format = 'H264'

    ffmpeg.format = 'WAV'
    ffmpeg.audio_codec = 'PCM'
    ffmpeg.audio_bitrate = 192

def save_scene_settings(context):
    scene = context.scene
    render = scene.render
    image = render.image_settings
    ffmpeg = render.ffmpeg
    props = scene.oha_layout_tools

    props.scene_frame_start =  scene.frame_start
    props.scene_frame_end = scene.frame_end

    props.render_filepath = render.filepath
    props.image_file_format = image.file_format

    props.ffmpeg_format = ffmpeg.format
    props.ffmpeg_audio_codec = ffmpeg.audio_codec
    props.ffmpeg_audio_bitrate = ffmpeg.audio_bitrate

def restore_scene_settings(context):
    scene = context.scene
    render = scene.render
    image = render.image_settings
    ffmpeg = render.ffmpeg
    props = scene.oha_layout_tools

    scene.frame_start = props.scene_frame_start
    scene.frame_end = props.scene_frame_end
    
    render.filepath = props.render_filepath
    image.file_format = props.image_file_format

    ffmpeg.format = props.ffmpeg_format
    ffmpeg.audio_codec = props.ffmpeg_audio_codec
    ffmpeg.audio_bitrate = props.ffmpeg_audio_bitrate


# =========================== addon interface ==========================

@persistent
def render_pre_handler(dummy):
    props = bpy.context.scene.oha_layout_tools

    if props.render_marker_infos:
        rmi = props.render_marker_infos.pop(0)
        marker_scene_settings(bpy.context, rmi)

@persistent
def render_complete_handler(dummy):
    props = bpy.context.scene.oha_layout_tools

    if props.render_marker_infos:
        rmi = props.render_marker_infos.pop(0)
        marker_scene_settings(bpy.context, rmi)

        bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
    else:
        bpy.app.handlers.render_pre.remove(render_pre_handler)
        bpy.app.handlers.render_complete.remove(render_complete_handler)
        props.marker_infos.clear()
        props.render_marker_infos.clear()

def sequencer_headerbutton(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.operator('sequencer.oha_extract_shot_files', icon='ALIGN',
                 text='Extract')

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.oha_layout_tools = bpy.props.PointerProperty(
        type = OHA_LayoutToolsProps)
    bpy.types.SEQUENCER_HT_header.append(sequencer_headerbutton)

def unregister():
    bpy.utils.unregister_module(__name__)

    del bpy.types.Scene.oha_layout_tools
    bpy.types.SEQUENCER_HT_header.remove(sequencer_headerbutton)
    
