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
import zipfile
import xml.dom
from bpy.app.handlers import persistent

bl_info = {
    "name": "OHA Layout Tools",
    "author": "Adhi Hargo",
    "version": (1, 0, 2),
    "blender": (2, 71, 0),
    "location": "Sequencer > Tools > OHA Layout Tools",
    "description": "Create layout files.",
    "warning": "",
    "wiki_url": "https://github.com/adhihargo/layout_tools",
    "tracker_url": "https://github.com/adhihargo/layout_tools/issues",
    "category": "Sequencer"}


# ========== constants for Open Document Spreadsheet creation ==========
CONTENT_FN = "content.xml"
CONTENT_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:style", "urn:oasis:names:tc:opendocument:xmlns:style:1.0"),
    ("xmlns:text", "urn:oasis:names:tc:opendocument:xmlns:text:1.0"),
    ("xmlns:table", "urn:oasis:names:tc:opendocument:xmlns:table:1.0"),
    ("xmlns:fo", "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"),
    ("xmlns:meta", "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"),
    ("office:version", "1.2")])
SETTINGS_FN = "settings.xml"
SETTINGS_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
    ("xmlns:config", "urn:oasis:names:tc:opendocument:xmlns:config:1.0"),
    ("xmlns:ooo", "http://openoffice.org/2004/office"),
    ("office:version", "1.2")])
META_FN = "meta.xml"
META_DOCATTRS = set([
    ("xmlns:office", "urn:oasis:names:tc:opendocument:xmlns:office:1.0"),
    ("xmlns:xlink", "http://www.w3.org/1999/xlink"),
    ("xmlns:dc", "http://purl.org/dc/elements/1.1/"),
    ("xmlns:meta", "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"),
    ("xmlns:ooo", "http://openoffice.org/2004/office"),
    ("xmlns:grddl", "http://www.w3.org/2003/g/data-view#"),
    ("office:version", "1.2")])
MANIFEST_FN = "META-INF/manifest.xml"
MANIFEST_DATA = r'''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
 <manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>'''
MIMETYPE_FN = "mimetype"
MIMETYPE_DATA = "application/vnd.oasis.opendocument.spreadsheet"
STYLES_FN = "styles.xml"

class OHA_LayoutToolsProps(bpy.types.PropertyGroup):
    render_marker_infos = []
    marker_infos = []


# ============================== operators =============================

class ExtractShotfiles_Base():
    blendpath = None            # path of .blend file to restore back to
    render_basepath = None      # base path of layout files
    render_selected = False

    _timer = None

    scene_frame_start = None
    scene_frame_end = None

    render_filepath = None
    render_display_mode = None

    @classmethod
    def poll(self, context):
        props = context.scene.oha_layout_tools

        # The operator needs the scene to be already saved in a file,
        # and there's no unrendered shot marker.
        return context.blend_data.is_saved\
            and not props.render_marker_infos

    def write_shot_files(self, context):
        scene = context.scene
        props = scene.oha_layout_tools
        sequences = scene.sequence_editor.sequences
        scene.timeline_markers.clear()
    
        self.restore_scene_settings(context)
        bpy.ops.sequencer.select_all(action='SELECT')
        bpy.ops.sequencer.delete()
        for mi in props.marker_infos:
            if (self.render_selected and not mi['select']):
                continue

            soundpath = os.path.join(self.render_basepath, 'sounds',
                                     mi['name']+'.wav')
            if not os.path.exists(soundpath):
                continue

            seq = None
            duration = mi['end'] - (mi['start']+1)
            scene.frame_end = scene.frame_start + duration
    
            seq = sequences.new_sound(mi['name'], soundpath,
                                      1, scene.frame_start)
    
            layoutdir = os.path.join(self.render_basepath, 'layouts')
            markerpath = bpy.path.ensure_ext(
                filepath=os.path.join(layoutdir, mi['name']), ext=".blend")
            bpy.ops.wm.save_as_mainfile(filepath=markerpath, copy=True,
                                        relative_remap=True)
            if seq:
                sequences.remove(seq)

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
            markers, [m.frame for m in markers[1:]]+[scene.frame_end]):
            props.marker_infos.append({'name':m.name,
                                      'select':m.select,
                                      'start':m.frame,
                                      'end':frame_end})

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
            context.area.header_text_set()
            bpy.ops.wm.open_mainfile(filepath=self.blendpath)

    def save_scene_settings(self, context):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg
        props = scene.oha_layout_tools
    
        self.scene_frame_start =  scene.frame_start
        self.scene_frame_end = scene.frame_end
    
        self.render_display_mode = render.display_mode
    
    def restore_scene_settings(self, context):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg
        props = scene.oha_layout_tools
    
        scene.frame_start = self.scene_frame_start
        scene.frame_end = self.scene_frame_end
        
        render.display_mode = self.render_display_mode
    
    def marker_scene_settings(self, context, mi):
        scene = context.scene
        render = scene.render
        image = render.image_settings
        ffmpeg = render.ffmpeg
        props = scene.oha_layout_tools
    
        scene.frame_current = scene.frame_start =  mi['start']
        scene.frame_end = mi['end']
    
        self.render_filepath = os.path.join(self.render_basepath, 'sounds',
                                            mi['name']+'.wav')
        render.display_mode = 'NONE'
    
    def invoke(self, context, event):
        scene = context.scene
        props = scene.oha_layout_tools

        self.render_selected = event.shift == True

        self.blendpath = bpy.path.abspath(context.blend_data.filepath)

        self.init_marker_infos(context)
        if not props.marker_infos:
            return self.cancel(context)
        adjust_duration_to_effects(context)
        
        blenddir, blendfile = os.path.split(self.blendpath)
        blenddir0, blenddir1 = os.path.split(blenddir)
        blendfile_base = os.path.splitext(blendfile)[0]

        self.render_basepath = os.path.join(blenddir0, blendfile_base)
        layoutdir = os.path.join(self.render_basepath, 'layouts')
        if not os.path.exists(layoutdir):
            os.makedirs(layoutdir)

        write_shot_listing_ods(props,
                               os.path.join(blenddir, blendfile_base + '.ods'))
        self.save_scene_settings(context)

        return self.execute(context)


class SEQUENCER_OT_ExtractShotfiles(ExtractShotfiles_Base, bpy.types.Operator):
    '''Automatically create layout files using marker boundaries.'''
    bl_idname = 'sequencer.oha_extract_shot_files'
    bl_label = 'Create Layout'
    bl_options = {'REGISTER'}

    prev_stat = None

    def check_render_file(self, context):
        wm = context.window_manager
        scene = context.scene
        props = scene.oha_layout_tools
        context.area.tag_redraw()

        if not self.prev_stat:
            self.prev_stat = os.stat(self.render_filepath)

            return {'PASS_THROUGH'}

        cur_stat = os.stat(self.render_filepath)

        if self.prev_stat.st_size != cur_stat.st_size:
            self.prev_stat = cur_stat

            return {'PASS_THROUGH'}

        self.render_complete_handler(context)

        if props.render_marker_infos:
            self.render_pre_handler(context)
            self.prev_stat = None
            bpy.ops.sound.mixdown('INVOKE_DEFAULT', filepath=self.render_filepath,
                                  container='WAV')

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

        wm.modal_handler_add(self)
        self._timer = wm.event_timer_add(2.0, context.window)

        if props.render_marker_infos:
            self.render_pre_handler(context)
            bpy.ops.sound.mixdown('INVOKE_DEFAULT', filepath=self.render_filepath,
                                  container='WAV')

            return {'RUNNING_MODAL'}

        return {'FINISHED'}



# ========================= auxiliary functions ========================

def write_shot_listing_txt(props, lpath):
    # Write the duration of each shots (difference of adjacent
    # markers) to a text file.
    lfile = open(lpath, 'w')
    for mi in props.marker_infos:
        lfile.write("%s:\t%s frames.\n" % (mi['name'],
                                           mi['end'] - mi['start']))
    lfile.close()

def write_shot_listing_ods(props, lpath):
    doc = zipfile.ZipFile(lpath, "w", zipfile.ZIP_DEFLATED)

    doc.writestr(MIMETYPE_FN, MIMETYPE_DATA, zipfile.ZIP_STORED)
    doc.writestr(MANIFEST_FN, MANIFEST_DATA)

    content_doc = xml.dom.getDOMImplementation().createDocument(
        "office", "office:document-content", None)
    for key, value in CONTENT_DOCATTRS:
        content_doc.documentElement.setAttribute(key, value)
    for element in ("office:scripts", "office:automatic-styles", "office:font-face-decls"):
        content_doc.documentElement.appendChild(content_doc.createElement(element))
    body = content_doc.createElement("office:body")
    spreadsheet = content_doc.createElement("office:spreadsheet")
    table = content_doc.createElement("table:table")
    column = content_doc.createElement("table:table-column")
    content_doc.documentElement.appendChild(body)
    body.appendChild(spreadsheet)
    spreadsheet.appendChild(table)
    table.appendChild(column)

    table.setAttribute("table:name", "Sheet1")
    for mi in props.marker_infos:
        framecount = str(mi['end'] - mi['start'])
        row = content_doc.createElement("table:table-row")

        cell1 = content_doc.createElement("table:table-cell")
        cell1.setAttribute("office:value-type", "string")
        text1 = content_doc.createElement("text:p")
        text1_data = content_doc.createTextNode(mi["name"])
        text1.appendChild(text1_data)
        cell1.appendChild(text1)

        cell2 = content_doc.createElement("table:table-cell")
        cell2.setAttribute("office:value-type", "float")
        cell2.setAttribute("office:value", framecount)
        text2 = content_doc.createElement("text:p")
        text2_data = content_doc.createTextNode(framecount)
        text2.appendChild(text2_data)
        cell2.appendChild(text2)

        table.appendChild(row)
        row.appendChild(cell1)
        row.appendChild(cell2)

    doc.writestr(CONTENT_FN, content_doc.toxml(encoding="UTF-8"))

    meta_doc = xml.dom.getDOMImplementation().createDocument(
        "office", "office:document-meta", None)
    for key, value in META_DOCATTRS:
        meta_doc.documentElement.setAttribute(key, value)
    meta = meta_doc.createElement("office:meta")
    meta_doc.documentElement.appendChild(meta)
    doc.writestr(META_FN, meta_doc.toxml(encoding="UTF-8"))

    settings_doc = xml.dom.getDOMImplementation().createDocument(
        "office", "office:document-settings", None)
    for key, value in SETTINGS_DOCATTRS:
        settings_doc.documentElement.setAttribute(key, value)
    settings = settings_doc.createElement("office:settings")
    settings_doc.documentElement.appendChild(settings)
    doc.writestr(SETTINGS_FN, settings_doc.toxml(encoding="UTF-8"))

    styles_doc = xml.dom.getDOMImplementation().createDocument(
        "office", "office:document-styles", None)
    for key, value in CONTENT_DOCATTRS:
        styles_doc.documentElement.setAttribute(key, value)
    styles = styles_doc.createElement("office:styles")
    styles_doc.documentElement.appendChild(styles)
    masterstyles = styles_doc.createElement("office:master-styles")
    styles_doc.documentElement.appendChild(masterstyles)
    autostyles = styles_doc.createElement("office:automatic-styles")
    styles_doc.documentElement.appendChild(autostyles)
    doc.writestr(STYLES_FN, styles_doc.toxml(encoding="UTF-8"))

    
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


# =========================== addon interface ==========================

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
    
