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

import csv
import os
import re
import xml.dom
import zipfile

import bpy
from bpy_extras.io_utils import ImportHelper

from . import constants


class ExtractShotfiles_Base():
    # This class contains the main shot initialization codes. Its
    # separation from the outermost operator class doing the actual
    # rendering, below, is to allow me to experiment with different
    # render monitoring methods. Otherwise they can be safely merged.
    blendpath = None  # path of .blend file to restore back to
    render_basepath = None  # base path of layout files
    render_selected = False

    _timer = None

    scene_frame_start = None
    scene_frame_end = None
    scene_use_audio = None

    render_filepath = None
    render_filepath_vid = None
    render_filepath_aud = None

    image_file_format = None

    ffmpeg_format = None
    ffmpeg_audio_codec = None
    ffmpeg_audio_bitrate = None

    @classmethod
    def poll(cls, context):
        props = context.scene.oha_layout_tools

        # The operator needs the scene to be already saved in a file,
        # and there's no unrendered shot marker.
        return context.blend_data.is_saved \
               and not props.render_marker_infos

    def write_shot_listing_csv(self, props, lpath):
        try:
            csvfile = open(lpath, "w", newline='')
        except:
            self.report({"WARNING"}, 'Unable to open "%s", shotlist not written.' % lpath)
            return

        csvwriter = csv.writer(csvfile, dialect="excel-tab", quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(["Shot", "Start", "End", "Duration"])
        for mi in props.marker_infos:
            csvwriter.writerow([mi['name'], mi['start'], mi['end'], mi['end'] - mi['start']])

        csvfile.close()

    def write_shot_listing_ods(self, props, lpath):
        try:
            doc = zipfile.ZipFile(lpath, "w", zipfile.ZIP_DEFLATED)
        except:
            self.report({"WARNING"}, 'Unable to open "%s", shotlist not written.' % lpath)
            return

        doc.writestr(constants.MIMETYPE_FN, constants.MIMETYPE_DATA, zipfile.ZIP_STORED)
        doc.writestr(constants.MANIFEST_FN, constants.MANIFEST_DATA)

        content_doc = xml.dom.getDOMImplementation().createDocument(
            "office", "office:document-content", None)
        content_element = content_doc.documentElement
        for key, value in constants.CONTENT_DOCATTRS:
            content_doc.documentElement.setAttribute(key, value)
        for element in ("office:scripts", "office:automatic-styles",
                        "office:font-face-decls"):
            content_doc.documentElement.appendChild(content_doc.createElement(element))
        body = content_doc.createElement("office:body")
        spreadsheet = content_doc.createElement("office:spreadsheet")
        table = content_doc.createElement("table:table")
        column = content_doc.createElement("table:table-column")
        content_element.appendChild(body)
        body.appendChild(spreadsheet)
        spreadsheet.appendChild(table)
        table.appendChild(column)

        # Insert header
        if True:
            row = content_doc.createElement("table:table-row")

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "string")
            # cell.setAttribute("table:style-name", "Heading")
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode("Shot")
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "string")
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode("Frame Start")
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "string")
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode("Frame End")
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "string")
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode("Duration")
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            table.appendChild(row)

        table.setAttribute("table:name", "Sheet1")
        for mi in props.marker_infos:
            framestart = str(mi['start'])
            frameend = str(mi['end'])
            framecount = str(mi['end'] - mi['start'])
            row = content_doc.createElement("table:table-row")

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "string")
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode(mi["name"])
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "float")
            cell.setAttribute("office:value", framestart)
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode(framestart)
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "float")
            cell.setAttribute("office:value", frameend)
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode(frameend)
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            cell = content_doc.createElement("table:table-cell")
            cell.setAttribute("office:value-type", "float")
            cell.setAttribute("office:value", framecount)
            text = content_doc.createElement("text:p")
            text_data = content_doc.createTextNode(framecount)
            text.appendChild(text_data)
            cell.appendChild(text)
            row.appendChild(cell)

            table.appendChild(row)

        doc.writestr(constants.CONTENT_FN, content_doc.toxml(encoding="UTF-8"))

        meta_doc = xml.dom.getDOMImplementation().createDocument(
            "office", "office:document-meta", None)
        for key, value in constants.META_DOCATTRS:
            meta_doc.documentElement.setAttribute(key, value)
        meta = meta_doc.createElement("office:meta")
        meta_doc.documentElement.appendChild(meta)
        doc.writestr(constants.META_FN, meta_doc.toxml(encoding="UTF-8"))

        settings_doc = xml.dom.getDOMImplementation().createDocument(
            "office", "office:document-settings", None)
        for key, value in constants.SETTINGS_DOCATTRS:
            settings_doc.documentElement.setAttribute(key, value)
        settings = settings_doc.createElement("office:settings")
        settings_doc.documentElement.appendChild(settings)
        doc.writestr(constants.SETTINGS_FN, settings_doc.toxml(encoding="UTF-8"))

        styles_doc = xml.dom.getDOMImplementation().createDocument(
            "office", "office:document-styles", None)
        for key, value in constants.CONTENT_DOCATTRS:
            styles_doc.documentElement.setAttribute(key, value)
        styles = styles_doc.createElement("office:styles")
        styles_doc.documentElement.appendChild(styles)
        masterstyles = styles_doc.createElement("office:master-styles")
        styles_doc.documentElement.appendChild(masterstyles)
        autostyles = styles_doc.createElement("office:automatic-styles")
        styles_doc.documentElement.appendChild(autostyles)
        doc.writestr(constants.STYLES_FN, styles_doc.toxml(encoding="UTF-8"))

    def write_shot_files(self, context):
        scene = context.scene
        props = scene.oha_layout_tools
        prefs = context.preferences.addons[__package__].preferences
        sequences = scene.sequence_editor.sequences
        scene.timeline_markers.clear()

        self.restore_scene_settings(context)
        bpy.ops.sequencer.select_all(action='SELECT')
        bpy.ops.sequencer.delete()
        for mi in props.marker_infos:
            if (self.render_selected and not mi['select']):
                continue

            seq = None
            seq2 = None
            path = os.path.join(self.render_basepath, 'sounds',
                                mi['name'] + '.mov') if prefs.is_render_video else \
                os.path.join(self.render_basepath, 'sounds',
                             mi['name'] + '.wav')
            if not os.path.exists(path):
                continue

            if prefs.is_render_video:  # Add video strip
                duration = mi['end'] - (mi['start'] + 1)
                scene.frame_end = scene.frame_start + duration

                seq = sequences.new_sound(mi['name'], path,
                                          1, scene.frame_start)
                seq2 = sequences.new_movie(mi['name'], path,
                                           2, scene.frame_start)
            else:  # Add sound strip
                duration = mi['end'] - (mi['start'] + 1)
                scene.frame_end = scene.frame_start + duration

                seq = sequences.new_sound(mi['name'], path,
                                          1, scene.frame_start)

            layoutdir = os.path.join(self.render_basepath, 'layouts')
            markerpath = bpy.path.ensure_ext(
                filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
            bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                        relative_remap=True)

            # Remove strips, prepare for next file
            if seq:
                sequences.remove(seq)
            if seq2:
                sequences.remove(seq2)

    def init_marker_infos(self, context):
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
                markers, [m.frame for m in markers[1:]] + [scene.frame_end]):
            props.marker_infos.append({'name': m.name,
                                       'select': m.select,
                                       'start': m.frame,
                                       'end': frame_end})

        props.render_marker_infos.clear()
        props.render_marker_infos.extend(
            [mi for mi in props.marker_infos if mi['select'] == True]
            if self.render_selected else props.marker_infos)

    def render_pre_handler(self, context):
        props = bpy.context.scene.oha_layout_tools

        if props.render_marker_infos:
            rmi = props.render_marker_infos.pop(0)
            rmi_idx = props.marker_infos.index(rmi) + 1
            context.area.header_text_set(
                'Rendering shot "%s" (%d of %d, %d frames)' %
                (rmi['name'], rmi_idx, len(props.marker_infos),
                 rmi['end'] - rmi['start']))
            context.area.tag_redraw()
            self.marker_scene_settings(context, rmi)

    def render_complete_handler(self, context):
        props = context.scene.oha_layout_tools

        if not props.render_marker_infos:
            self.write_shot_files(context)
            props.marker_infos.clear()
            context.area.header_text_set(None)
            bpy.ops.wm.open_mainfile(filepath=self.blendpath)

    def save_scene_settings(self, context):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg

        self.scene_frame_start = scene.frame_start
        self.scene_frame_end = scene.frame_end
        self.scene_use_audio = scene.use_audio

        self.render_filepath = render.filepath

        self.image_file_format = image.file_format

        self.ffmpeg_format = ffmpeg.format
        self.ffmpeg_audio_codec = ffmpeg.audio_codec
        self.ffmpeg_audio_bitrate = ffmpeg.audio_bitrate

    def restore_scene_settings(self, context):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg

        scene.frame_start = self.scene_frame_start
        scene.frame_end = self.scene_frame_end
        scene.use_audio = self.scene_use_audio

        render.filepath = self.render_filepath

        image.file_format = self.image_file_format
        ffmpeg.format = self.ffmpeg_format
        ffmpeg.audio_codec = self.ffmpeg_audio_codec
        ffmpeg.audio_bitrate = self.ffmpeg_audio_bitrate

    def marker_scene_settings(self, context, mi):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg

        scene.frame_start = mi['start']
        scene.frame_end = mi['end']
        scene.use_audio = False  # Audio mustn't be muted upon mixdown.

        self.render_filepath_vid = os.path.join(self.render_basepath, 'sounds',
                                                mi['name'] + '.mov')
        self.render_filepath_aud = os.path.join(self.render_basepath, 'sounds',
                                                mi['name'] + '.wav')
        render.filepath = self.render_filepath_vid

        image.file_format = "FFMPEG"

        ffmpeg.format = 'QUICKTIME'
        ffmpeg.audio_codec = 'MP3'
        ffmpeg.audio_bitrate = 192

    def invoke(self, context, event):
        scene = context.scene
        props = scene.oha_layout_tools
        prefs = context.preferences.addons[__package__].preferences

        self.render_selected = (event.shift is True)

        if not context.blend_data.is_saved:
            self.report({"ERROR"}, "Could not extract from unsaved file.")
            return {"CANCELLED"}
        self.blendpath = bpy.path.abspath(context.blend_data.filepath)

        self.init_marker_infos(context)
        if not props.marker_infos:
            return self.cancel(context)
        adjust_duration_to_effects(context)

        blenddir, blendfile = os.path.split(self.blendpath)
        blendname = os.path.splitext(blendfile)[0]
        template_str = re.sub(r"(%\([^)]+\))", r"\1s", prefs.layout_path.strip())
        template_dict = dict(blendname=blendname)
        self.render_basepath = os.path.abspath(
            os.path.join(blenddir, template_str % template_dict))

        if not os.path.exists(self.render_basepath):
            try:
                os.makedirs(self.render_basepath)
            except:
                self.report({"ERROR"}, "Unable to create layout directory.")

        layoutdir = os.path.join(self.render_basepath, 'layouts')
        if not os.path.exists(layoutdir):
            os.makedirs(layoutdir)
        sounddir = os.path.join(self.render_basepath, 'sounds')
        if not os.path.exists(sounddir):
            os.makedirs(sounddir)

        if prefs.is_export_ods:
            self.write_shot_listing_ods(
                props, os.path.join(blenddir, blendname + '.ods'))
        if prefs.is_export_csv:
            self.write_shot_listing_csv(
                props, os.path.join(blenddir, blendname + '.txt'))
        self.save_scene_settings(context)

        return self.execute(context)


class SEQUENCER_OT_ExtractShotfiles(ExtractShotfiles_Base, bpy.types.Operator):
    '''Automatically create layout files using marker boundaries. Press SHIFT+click to only extract selected marker/s'''
    bl_idname = 'sequencer.oha_extract_shot_files'
    bl_label = 'Create Layout'
    bl_options = {'REGISTER'}

    prev_stat = None

    def check_render_file(self, context):
        wm = context.window_manager
        scene = context.scene
        props = scene.oha_layout_tools
        prefs = context.preferences.addons[__package__].preferences
        context.area.tag_redraw()

        file_stat = self.render_filepath_vid if prefs.is_render_video \
            else self.render_filepath_aud

        if not self.prev_stat:
            self.prev_stat = os.stat(file_stat)
            return {'PASS_THROUGH'}

        cur_stat = os.stat(file_stat)

        if self.prev_stat.st_size != cur_stat.st_size:
            self.prev_stat = cur_stat
            return {'PASS_THROUGH'}

        self.render_complete_handler(context)

        if props.render_marker_infos:
            self.render_pre_handler(context)
            self.prev_stat = None
            if prefs.is_render_video:
                bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
            else:
                bpy.ops.sound.mixdown('INVOKE_DEFAULT', filepath=self.render_filepath_aud,
                                      container='WAV', codec="PCM")

            return {'PASS_THROUGH'}

        return {'FINISHED'}

    def modal(self, context, event):
        wm = context.window_manager
        props = context.scene.oha_layout_tools

        if event.type == 'TIMER':
            return self.check_render_file(context)
        elif event.type == 'ESC':
            props.render_marker_infos.clear()
            self.render_complete_handler(context)

            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        props = scene.oha_layout_tools
        prefs = context.preferences.addons[__package__].preferences

        if not self.blendpath:
            self.report({"ERROR"}, "Could not extract from unsaved file.")
            return {"CANCELLED"}

        wm.modal_handler_add(self)
        self._timer = wm.event_timer_add(time_step=2.0, window=context.window)

        if props.render_marker_infos:
            self.render_pre_handler(context)
            if prefs.is_render_video:
                bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
            else:
                bpy.ops.sound.mixdown('INVOKE_DEFAULT', filepath=self.render_filepath_aud,
                                      container='WAV', codec="PCM")

            return {'RUNNING_MODAL'}

        return {'FINISHED'}


class SCENE_OT_ImportAssets(bpy.types.Operator, ImportHelper):
    """Import all assets from other .blend file"""
    bl_idname = "scene.oha_import"
    bl_label = "Import Assets"

    # ImportHelper mixin class uses this
    filename_ext = ".blend"

    filter_glob: bpy.props.StringProperty(
        default="*.blend",
        options={'HIDDEN'},
    )

    is_import_scs: bpy.props.BoolProperty(
        name="Scene Settings",
        default=True,
    )
    is_import_res: bpy.props.BoolProperty(
        name="Render Settings",
        default=True,
    )
    is_import_cam: bpy.props.BoolProperty(
        name="Camera",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Extra Settings to Copy:")
        col = layout.column_flow(columns=2, align=True)
        col.prop(self, "is_import_scs", toggle=True)
        col.prop(self, "is_import_res", toggle=True)

        layout.label(text="Extra Object Type to Copy:")
        col = layout.column_flow(columns=2, align=True)
        col.prop(self, "is_import_cam", toggle=True)

    def import_assets(self, context, scene_name):
        cur_scene = context.scene
        old_scene = bpy.data.scenes.get(scene_name, None)
        if old_scene:
            old_scene.name = scene_name + ".orig"

        od = dict(filepath=self.filepath, obj=scene_name, sep=os.sep)
        scene_dirpath = "%(filepath)s%(sep)sScene%(sep)s" % od
        scene_filepath = scene_dirpath + scene_name

        bpy.ops.wm.append(
            directory=scene_dirpath,
            filepath=scene_filepath,
            filename=scene_name,
            filemode=1,
            link=False,
            autoselect=False,)
        new_scene = bpy.data.scenes[scene_name]

        if self.is_import_scs:
            for attr in ["frame_step", "layers", "sync_mode", "use_audio", "use_audio_scrub",
                         "use_audio_sync", "use_frame_drop", "use_nodes"]:
                if not getattr(cur_scene, attr, None):
                    continue
                setattr(cur_scene, attr, getattr(new_scene, attr))

        if self.is_import_res:
            for attr in ['alpha_mode', 'antialiasing_samples', 'bake_aa_mode', 'bake_bias',
                         'bake_distance', 'bake_margin', 'bake_normal_space',
                         'bake_quad_split', 'bake_samples', 'bake_type', 'bake_user_scale',
                         'border_max_x', 'border_max_y', 'border_min_x', 'border_min_y',
                         'display_mode', 'dither_intensity', 'edge_color', 'edge_threshold',
                         'engine', 'field_order', 'filepath', 'filter_size',
                         'fps', 'fps_base', 'frame_map_new', 'frame_map_old',
                         'line_thickness', 'line_thickness_mode', 'motion_blur_samples',
                         'motion_blur_shutter', 'octree_resolution',
                         'pixel_aspect_x', 'pixel_aspect_y', 'pixel_filter_type',
                         'preview_start_resolution', 'raytrace_method',
                         'resolution_percentage', 'resolution_x', 'resolution_y',
                         'sequencer_gl_preview', 'sequencer_gl_render',
                         'threads', 'threads_mode', 'tile_x', 'tile_y',
                         'use_antialiasing', 'use_border', 'use_compositing',
                         'use_crop_to_border', 'use_edge_enhance', 'use_envmaps',
                         'use_fields', 'use_fields_still', 'use_file_extension',
                         'use_free_image_textures', 'use_free_unused_nodes', 'use_freestyle',
                         'use_full_sample', 'use_instances', 'use_local_coords',
                         'use_lock_interface', 'use_motion_blur', 'use_overwrite',
                         'use_persistent_data', 'use_placeholder', 'use_raytrace',
                         'use_render_cache', 'use_save_buffers', 'use_sequencer',
                         'use_sequencer_gl_preview', 'use_sequencer_gl_textured_solid',
                         'use_shadows', 'use_simplify', 'use_simplify_triangulate',
                         'use_single_layer', 'use_sss', 'use_textures']:
                if not getattr(cur_scene.render, attr, None):
                    continue
                print("ATTR: %s", attr)
                setattr(cur_scene.render, attr, getattr(new_scene.render, attr))
            for attr in ['aa_samples', 'ao_samples', 'bake_type', 'blur_glossy',
                         'caustics_reflective', 'caustics_refractive', 'device',
                         'diffuse_bounces', 'diffuse_samples', 'feature_set',
                         'film_exposure', 'film_transparent', 'filter_type', 'filter_width',
                         'glossy_bounces', 'glossy_samples', 'max_bounces',
                         'mesh_light_samples', 'min_bounces', 'preview_aa_samples',
                         'preview_active_layer', 'preview_pause', 'preview_samples',
                         'preview_start_resolution', 'progressive',
                         'sample_all_lights_direct', 'sample_all_lights_indirect',
                         'sample_clamp_direct', 'sample_clamp_indirect', 'samples',
                         'sampling_pattern', 'seed', 'shading_system', 'subsurface_samples',
                         'tile_order', 'transmission_bounces', 'transmission_samples',
                         'transparent_max_bounces', 'transparent_min_bounces', 'use_cache',
                         'use_layer_samples', 'use_progressive_refine', 'use_samples_final',
                         'use_square_samples', 'use_transparent_shadows', 'volume_bounces',
                         'volume_max_steps', 'volume_samples', 'volume_step_size']:
                if not getattr(cur_scene.cycles, attr, None):
                    continue
                setattr(cur_scene.cycles, attr, getattr(new_scene.cycles, attr))
            for attr in ['cineon_black', 'cineon_gamma', 'cineon_white', 'color_depth',
                         'color_mode', 'compression', 'exr_codec', 'file_format',
                         'jpeg2k_codec', 'quality', 'use_cineon_log',
                         'use_jpeg2k_cinema_48', 'use_jpeg2k_cinema_preset',
                         'use_jpeg2k_ycc', 'use_preview', 'use_zbuffer']:
                if not getattr(cur_scene.render.image_settings, attr, None):
                    continue
                setattr(cur_scene.render.image_settings, attr,
                        getattr(new_scene.render.image_settings, attr))

        for obj in new_scene.objects:
            if not self.is_import_cam and getattr(obj, "type", None) == "CAMERA":
                continue

            obj.select = False
            cur_scene.objects.link(obj)
        cur_scene.update()

        if old_scene:
            new_scene.name = scene_name + ".001"
            old_scene.name = scene_name
        bpy.data.scenes.remove(new_scene)

    def execute(self, context):
        scene_list = []
        with bpy.data.libraries.load(self.filepath) as (data_from, data_to):
            scene_list.extend(data_from.scenes)

        for scene_name in scene_list:
            self.import_assets(context, scene_name)

        return {'FINISHED'}


class SCENE_OT_RenameMarkers(bpy.types.Operator):
    """Automatically name the marker, ascending in number"""
    # Auto marker renamer with additional Blender file name on it
    bl_idname = "scene.rename_markers"
    bl_label = "Rename Markers"

    def execute(self, context):
        self.blendpath = bpy.path.abspath(context.blend_data.filepath)
        blenddir, blendfile = os.path.split(self.blendpath)
        blendname = os.path.splitext(blendfile)[0]

        for i, marker in enumerate(sorted(context.scene.timeline_markers, key=lambda m: m.frame), 1):
            marker.name = blendname + '_' + str(i).zfill(3)
        return {'FINISHED'}


class OBJECT_OT_ProxyMakeAll(bpy.types.Operator):
    """Make proxies from all selected objects"""
    bl_idname = "object.proxy_make_all"
    bl_label = "Make Proxies"

    def execute(self, context):
        for obj in context.selected_objects:
            context.view_layer.objects.active = obj  # make it the context object
            bpy.ops.object.proxy_make(object="DEFAULT")
        return {'FINISHED'}


def adjust_duration_to_effects(context):
    scene = context.scene
    props = scene.oha_layout_tools
    sequences = scene.sequence_editor.sequences

    effects = [seq for seq in sequences
               if isinstance(seq, bpy.types.EffectSequence)
               and seq.type in ['CROSS', 'ADD', 'SUBTRACT', 'ALPHA_OVER',
                                'ALPHA_UNDER', 'GAMMA_CROSS', 'MULTIPLY',
                                'OVER_DROP', 'WIPE']]
    for mi in props.marker_infos:
        overlap_start = [e for e in effects
                         if mi['start'] == e.frame_final_end]
        overlap_end = [e for e in effects
                       if mi['end'] == e.frame_final_start]
        if overlap_start:
            mi['start'] = overlap_start[0].frame_final_start
        if overlap_end:
            mi['end'] = overlap_end[0].frame_final_end
