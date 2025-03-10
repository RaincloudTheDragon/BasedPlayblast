
bl_info = {
    "name": "Playblast_Animation_Plugin_Ver2_3",
    "author": "Somebody wants told me",
    "version": (2, 3),
    "blender": (2, 90, 1),
    "location": "View3D > Sidebar > Playblast",
    "description": "Preview animation",
    "warning": "",
    "doc_url": "",
    "category": "Animation"
}

import bpy
from bpy.types import Operator

from bpy.props import (
    EnumProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty
)

default_file_path = "/tmp\\"
default_file_name = ""
tmpImageFileFormat = 'PNG'

bpy.types.WindowManager.resolutionMode = 'LIST'
bpy.types.WindowManager.settings_resolutionX = 800
bpy.types.WindowManager.settings_resolutionY = 540
bpy.types.WindowManager.resolution_percentage = 100
bpy.types.WindowManager.settings_displayResolution = True

bpy.types.WindowManager.settings_extra_info = ""
bpy.types.WindowManager.settings_autoDisableOverlays = True

bpy.types.Scene.output_file_path   = default_file_path
bpy.types.Scene.output_file_name   = default_file_name
bpy.types.Scene.saveOutputToFile   = True
bpy.types.Scene.image_file_format  = tmpImageFileFormat 
bpy.types.Scene.isVideoFile        = True
bpy.types.Scene.output_encoding    = 'QUICKTIME'
bpy.types.Scene.ffmpeg_codec       = 'H264'
bpy.types.Scene.output_quality     = 'MEDIUM'
bpy.types.Scene.ffmpeg_preset      = 'REALTIME'


bpy.types.Scene.audio_codec        = 'NONE'
bpy.types.Scene.audio_bitrate      = 192
bpy.types.Scene.audio_volume       = 1.0

bpy.types.Scene.use_stamp_camera   = False
bpy.types.Scene.use_stamp_lens     = False
bpy.types.Scene.use_stamp_scene    = True

class PlayblastSettings(Operator):
    bl_idname = "my.playblast_settings"
    bl_label  = "Playblast Settings"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    
    resolutionModeContainer = (
        ('SYNC',   "Use Scene Resolution", ""),
        ('LIST',   "Resolution List", ""),
        ('CUSTOM', "Custom Resolution", ""),
    )
    resolutionMode: EnumProperty(
        name="Resolution Mode",
        items=resolutionModeContainer,
        default='LIST'
    )
    
    resolutionTemplateContainer = (
        ('x1920y1080', "1920 x 1080 (16:9) HD1080p", ""),
        ('x1280y720', "1280 x 720 (16:9) HD720p", ""),
        ('x848y480',"854 x 480 (16:9) 480P", ""),
        ('x640y360', "640 x 360 (16:9) 360P", ""),
        ('x1920y1440', "1920 x 1440 (4:3)", ""),
        ('x1600y1200', "1600 x 1200 (4:3)", ""),
        ('x1280y960', "1280 x 960 (4:3)", ""),
        ('x1024y768', "1024 x 768 (4:3)", ""),
        ('x960y720', "960 x 720 (4:3)", ""),
        ('x800y600', "800 x 600 (4:3)", ""),
        ('x640y480', "640 x 480 (4:3)", ""),
        ('x1024y1024', "1024 x 1024 (1:1)", ""),
        ('x512y512', "512 x 512 (1:1)", ""),
        ('x200y200', "200 x 200 (1:1)", "")        
    )
    
    resolutionTemplate: EnumProperty(
        name="Resolution List",
        items=resolutionTemplateContainer,
        default='x1920y1080',
        
    )
        
    resolutionX : IntProperty(
        name="Resolution X",
        subtype='PIXEL',
        default=1920,
        min=4,
        
    )
    
    resolutionY : IntProperty(
        name="Resolution Y",
        subtype='PIXEL',
        default=1080,
        min=4,
        
    )
    
    resolution_percentage : IntProperty(
        name="Resolution %",
        subtype='PERCENTAGE',
        default=50,
        min=1,
        
    )

    outputFilePath : StringProperty(
        name="File Path",
        subtype="FILE_PATH",
        default="/tmp\\"
    )
    outputFileName : StringProperty(
        name="File Name",
        default=""
    )
    
    saveOutputToFile : BoolProperty(
        name="Save to file",
        default=True,
        
    )
    
    encodingContainer = (
        ('QUICKTIME',   "Quicktime", ""),
        ('MPEG4',       "MPEG-4", ""),
        ('AVI',         "AVI", ""),
        ('OGG',         "Ogg", ""),
        ('MKV',         "Matroska", ""),
        ('IMAGE',       "Image", "")
    )
    outputEncoding: EnumProperty(
        name="Format",
        items=encodingContainer,
        default='QUICKTIME'
    )
    
    imageEncodingContainer = (
        ('PNG',        "png", ""),        
        ('JPEG',       "jpeg", ""),
        ('JPEG-2000',  "jpeg 2000", ""),
        ('CINEON',     "cineon", ""),
        ('DPX',        "dpx", ""),
        ('BMP',        "bmp", ""),
        ('TARGA',      "targa", ""),
        ('TIFF',       "tiff", "")
    )
    imageEncoding: EnumProperty(
        name="Encoding",
        items=imageEncodingContainer,
        default='PNG'
    )
    
    videoQualityContainer = (
        ('LOWEST',   "Lowest", ""),
        ('VERYLOW',  "Very low", ""),
        ('LOW',      "Low", ""),
        ('MEDIUM',   "Medium", ""),
        ('HIGH',     "High", "")
    )
    outputQuality: EnumProperty(
        name="Quality",
        items=videoQualityContainer,
        default='MEDIUM'
    )
    
    SolidmodeContainer = (
        ('MATERIAL',"Material",""),
        ('OBJECT',"Object",""),
        ('VERTEX',"Vertex",""),
        ('SINGLE',"Single",""),
        ('RANDOM',"Random",""),
        ('TEXTURE',"Texture",""),
    )
    SolidMode:EnumProperty(
        name="Material",
        items=SolidmodeContainer,
        default='MATERIAL'
    )
    
    ColorContainer = (
        ('WIREFRAME',"Wireframe",""),
        ('SOLID',"Solid",""),
        ('MATERIAL',"Material",""),
        ('RENDERED',"Rendered","")
    )
    ColorMode: EnumProperty(
        name="Material",
        items=ColorContainer,
        default='MATERIAL'
    )
    
    
    audioCodecContainer = (
        ('VORBIS', "Vorbis", ""),
        ('PCM',    "PCM", ""),
        ('OPUS',   "Opus", ""),
        ('MP3',    "MP3", ""),
        ('MP2',    "MP2", ""),
        ('FLAC',   "FLAC", ""),
        ('AC3',    "AC3", ""),
        ('AAC',    "AAC", ""),
        ('NONE',   "No Audio", "Disables audio outputs, for video-only"),
    )
    
    audioCodec: EnumProperty(
        name="Audio",
        items=audioCodecContainer,
        default='NONE',
        
    )
    
    audioBitrate: IntProperty(
         name="Bitrate",
         min=32,
         max=384,
         default=192,
         description="Audio bitrate (kb/s)"
    )
    
    audioVolume: FloatProperty(
        name="Volume",
        min=0.0,
        max=1.0,
        default=1.0,
        
    )
    
    extraInfo : StringProperty(
        name="Note",
        default="",
        
    )
    
    autoDisableOverlays : BoolProperty(
        name="Auto Disable Overlays",
        default=True,
        
    )
    
    # Metadata
    metadata_resolution : BoolProperty(
        name="Resolution",
        default=True,
        
    )
     
    metadata_camera_name : BoolProperty(
        name="Camera Name",
        default=False,
        
    )
    metadata_camera_lens : BoolProperty(
        name="Lens",
        default=False,
        
    )
    
    metadata_scene_name : BoolProperty(
        name="Scene Name",
        default=True,
        
    )
    
    
    # END
    
       
    def draw(self, context):      
        layout = self.layout
      
        layout.label(text="Resolution Settings")
        box = layout.box()
        box.prop(self, "resolutionMode", text="")
        if self.resolutionMode == 'LIST': 
            split = box.split()
            box = split.column(align = True)
            box.prop(self, "resolutionTemplate", text="", icon='PRESET')
        elif self.resolutionMode == 'CUSTOM':
            split = box.split()
            box = split.column(align = True)
            box.prop(self, "resolutionX")
            box.prop(self, "resolutionY")
            box.prop(self, "resolution_percentage")
        
        layout.label(text="Output Settings", icon='OUTPUT')
        box = layout.box()
        if self.saveOutputToFile:
            box.prop(self, "outputFilePath")
            box.prop(self, "outputFileName")
 
        box.prop(self, "saveOutputToFile")
          
        if self.saveOutputToFile:
            layout.label(text="Video Settings", icon='OUTLINER_DATA_CAMERA')
            box = layout.box()
            col = box.column(align = True)
            col.prop(self, "outputEncoding")
            if self.outputEncoding != 'IMAGE':
                col.prop(self, "outputQuality")
            else:
                col.prop(self, "imageEncoding")
        
        layout.label(text="Audio Settings", icon='SOUND')
        box = layout.box()      
        box.prop(self, "audioCodec")
        if self.audioCodec != 'NONE':
            box = box.column()
            box.prop(self, "audioBitrate")
            box.prop(self, "audioVolume")
        
        layout.label(text="Metadata")
        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(self, "metadata_resolution")
        row.prop(self, "metadata_scene_name")
        row = col.row(align=True)
        row.prop(self, "metadata_camera_name")
        row.prop(self, "metadata_camera_lens")
        row = box.row()
        row.prop(self, "extraInfo")
        
        #This is a new function
        layout.label(text="Texture")
        box = layout.box()
        col = box.column(align = True)
        #box.prop(self, "ColorMode", text="Texture")
        col.prop(self, "ColorMode")
        if self.ColorMode == 'SOLID':
            col.prop(self, "SolidMode", text="Color")
        #This is a new function
            
        layout.prop(self, "autoDisableOverlays")
                
        
        
        
    
    def get_str_btw(self, s, f, b):
        par = s.partition(f)
        value = (par[2].partition(b))[0][:]
        return int(value)
    
    def execute(self, context):
        if self.resolutionMode == 'LIST':
            self.resolutionX = self.get_str_btw(self.resolutionTemplate, 'x', 'y')
            self.resolutionY = self.get_str_btw(self.resolutionTemplate, 'y', 'y')
            
            print("Res X", self.resolutionX, " Res Y", self.resolutionY)
        elif self.resolutionMode =='SYNC': 
            self.resolutionX = bpy.context.scene.render.resolution_x
            self.resolutionY = bpy.context.scene.render.resolution_y
            self.resolution_percentage = bpy.context.scene.render.resolution_percentage
            
            print("Res X", self.resolutionX, " Res Y", self.resolutionY)
        
        bpy.types.WindowManager.resolutionMode = self.resolutionMode     
        bpy.types.WindowManager.settings_resolutionX = self.resolutionX
        bpy.types.WindowManager.settings_resolutionY = self.resolutionY
        bpy.types.WindowManager.resolution_percentage = self.resolution_percentage        
        bpy.types.WindowManager.settings_displayResolution = self.metadata_resolution
        
        bpy.types.WindowManager.settings_extra_info = self.extraInfo
        bpy.types.WindowManager.settings_autoDisableOverlays = self.autoDisableOverlays
        
        if self.saveOutputToFile:
            bpy.types.Scene.output_file_path = self.outputFilePath
            bpy.types.Scene.output_file_name = self.outputFileName
        else:
            bpy.types.Scene.output_file_path = default_file_path
            bpy.types.Scene.output_file_name = default_file_name
          
        bpy.types.Scene.saveOutputToFile   = self.saveOutputToFile
        
        if self.outputEncoding != 'IMAGE':
            bpy.types.Scene.output_encoding = self.outputEncoding
            bpy.types.Scene.output_quality = self.outputQuality
            bpy.types.Scene.isVideoFile = True
        else:
            bpy.types.Scene.image_file_format = self.imageEncoding
            bpy.types.Scene.isVideoFile = False
        
        bpy.types.Scene.use_stamp_camera   = self.metadata_camera_name 
        bpy.types.Scene.use_stamp_lens     = self.metadata_camera_lens       
        bpy.types.Scene.use_stamp_scene    = self.metadata_scene_name
        
        bpy.types.Scene.audio_codec = self.audioCodec
        bpy.types.Scene.audio_bitrate = self.audioBitrate
        bpy.types.Scene.audio_volume = self.audioVolume
        
        
        if self.ColorMode != 'SOLID':
            bpy.context.space_data.shading.type = self.ColorMode
        else:
            bpy.context.space_data.shading.type = self.ColorMode
            bpy.context.space_data.shading.color_type = self.SolidMode

        
        return {'FINISHED'}

class Playblast(Operator):
    bl_idname = "my.playblast"
    bl_label  = "Playblast"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.playblast()
        return {'FINISHED'}
    
    def playblast(self):               
        before_render_resolutionX = bpy.context.scene.render.resolution_x
        before_render_resolutionY = bpy.context.scene.render.resolution_y
        before_resolution_percentage = bpy.context.scene.render.resolution_percentage
        before_render_use_overwrite = bpy.context.scene.render.use_overwrite
        before_render_filepath    = bpy.context.scene.render.filepath
        before_use_file_extension = bpy.context.scene.render.use_file_extension
        before_image_settings_file_format = bpy.context.scene.render.image_settings.file_format
        before_output_encoding    = bpy.context.scene.render.ffmpeg.format  
        before_ffmpeg_codec       = bpy.context.scene.render.ffmpeg.codec
        before_video_quality      = bpy.context.scene.render.ffmpeg.constant_rate_factor
        before_ffmpeg_preset      = bpy.context.scene.render.ffmpeg.ffmpeg_preset
        before_audio_codec        = bpy.context.scene.render.ffmpeg.audio_codec
        before_audio_bitrate      = bpy.context.scene.render.ffmpeg.audio_bitrate
        before_audio_volume       = bpy.context.scene.render.ffmpeg.audio_volume
        before_use_stamp_date     = bpy.context.scene.render.use_stamp_date
        before_use_stamp_time     = bpy.context.scene.render.use_stamp_time
        before_use_stamp_render_time = bpy.context.scene.render.use_stamp_render_time
        before_use_stamp_frame    = bpy.context.scene.render.use_stamp_frame
        before_use_stamp_frame_range = bpy.context.scene.render.use_stamp_frame_range
        before_use_stamp_memory   = bpy.context.scene.render.use_stamp_memory
        before_use_stamp_hostname = bpy.context.scene.render.use_stamp_hostname
        before_use_stamp_camera   = bpy.context.scene.render.use_stamp_camera
        before_use_stamp_lens     = bpy.context.scene.render.use_stamp_lens
        before_use_stamp_scene    = bpy.context.scene.render.use_stamp_scene
        before_use_stamp_marker   = bpy.context.scene.render.use_stamp_marker
        before_use_stamp_filename = bpy.context.scene.render.use_stamp_filename
        before_use_stamp_sequencer_strip = bpy.context.scene.render.use_stamp_sequencer_strip
        before_use_stamp_note     = bpy.context.scene.render.use_stamp_note
        before_stamp_note_text    = bpy.context.scene.render.stamp_note_text
        before_use_stamp          = bpy.context.scene.render.use_stamp
        before_show_overlays      = bpy.context.space_data.overlay.show_overlays
        
        
        if bpy.context.space_data.shading.type != 'SOLID':
            before_texture_dxd= bpy.context.space_data.shading.type
        else:
            before_texture_something = bpy.context.space_data.shading.color_type

        
        
        
        bpy.context.scene.render.use_overwrite = True
        bpy.context.scene.render.use_file_extension = True 
        bpy.context.scene.render.use_stamp_render_time = False
        bpy.context.scene.render.use_stamp_frame_range = False
        bpy.context.scene.render.use_stamp_memory = False
        bpy.context.scene.render.use_stamp_hostname = False
        bpy.context.scene.render.use_stamp_marker = False
        bpy.context.scene.render.use_stamp_filename = False
        bpy.context.scene.render.use_stamp_sequencer_strip = False

        # Resolution settings        
        if bpy.types.WindowManager.resolutionMode != 'SYNC': 
            bpy.context.scene.render.resolution_x = bpy.types.WindowManager.settings_resolutionX
            bpy.context.scene.render.resolution_y = bpy.types.WindowManager.settings_resolutionY
            bpy.context.scene.render.resolution_percentage = bpy.types.WindowManager.resolution_percentage
        else:
            bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_x
            bpy.context.scene.render.resolution_y = bpy.context.scene.render.resolution_y
            bpy.context.scene.render.resolution_percentage = bpy.context.scene.render.resolution_percentage
        
        # Output Settings
        bpy.context.scene.render.filepath = bpy.types.Scene.output_file_path        
        if len(bpy.types.Scene.output_file_name) > 0:
           bpy.context.scene.render.filepath += bpy.types.Scene.output_file_name + "_"
        
        if bpy.types.Scene.saveOutputToFile:       
                     
           if bpy.types.Scene.isVideoFile:
               bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
               bpy.context.scene.render.ffmpeg.format = bpy.types.Scene.output_encoding
               bpy.context.scene.render.ffmpeg.codec = bpy.types.Scene.ffmpeg_codec
               bpy.context.scene.render.ffmpeg.constant_rate_factor = bpy.types.Scene.output_quality
               bpy.context.scene.render.ffmpeg.ffmpeg_preset = bpy.types.Scene.ffmpeg_preset     
           else:
               bpy.context.scene.render.image_settings.file_format = bpy.types.Scene.image_file_format
  
          
           bpy.context.scene.render.ffmpeg.audio_codec = bpy.types.Scene.audio_codec
           bpy.context.scene.render.ffmpeg.audio_bitrate = bpy.types.Scene.audio_bitrate
           bpy.context.scene.render.ffmpeg.audio_volume = bpy.types.Scene.audio_volume
        else:
           bpy.context.scene.render.filepath = default_file_path
           bpy.context.scene.render.image_settings.file_format = 'PNG'
        
        
        bpy.context.scene.render.use_stamp_date = True
        bpy.context.scene.render.use_stamp_time = True
        bpy.context.scene.render.use_stamp_frame = True
        bpy.context.scene.render.use_stamp_camera = bpy.types.Scene.use_stamp_camera
        bpy.context.scene.render.use_stamp_lens = bpy.types.Scene.use_stamp_lens
        bpy.context.scene.render.use_stamp_scene = bpy.types.Scene.use_stamp_scene
        
        bpy.context.scene.render.use_stamp_note = True
        
        note = "Playblast"
        note += ", Blender Version: " + bpy.app.version_string

        if bpy.types.WindowManager.settings_displayResolution:
           resPercentage = bpy.context.scene.render.resolution_percentage / 100.0
           resX = int(bpy.context.scene.render.resolution_x * resPercentage)
           resY = int(bpy.context.scene.render.resolution_y * resPercentage)
           
           resXStr = str(resX)
           resYStr = str(resY)
           note += "\n" + "Resolution: " + resXStr + " x " + resYStr + " px"
           
           
        if len(bpy.types.WindowManager.settings_extra_info) != 0:
           note += "\n" + bpy.types.WindowManager.settings_extra_info
        
        bpy.context.scene.render.stamp_note_text = note
        
        bpy.context.scene.render.use_stamp = True
        
        
        if bpy.types.WindowManager.settings_autoDisableOverlays:
           bpy.context.space_data.overlay.show_overlays = False
        
        
        bpy.ops.render.opengl(animation=True)
        
        
        bpy.context.scene.render.ffmpeg.codec           = before_ffmpeg_codec
        bpy.context.scene.render.ffmpeg.constant_rate_factor = before_video_quality
        bpy.context.scene.render.ffmpeg.ffmpeg_preset   = before_ffmpeg_preset
        bpy.context.scene.render.ffmpeg.audio_codec     = before_audio_codec
        bpy.context.scene.render.ffmpeg.audio_bitrate   = before_audio_bitrate
        bpy.context.scene.render.ffmpeg.audio_volume    = before_audio_volume
        bpy.context.scene.render.resolution_x           = before_render_resolutionX
        bpy.context.scene.render.resolution_y           = before_render_resolutionY
        bpy.context.scene.render.resolution_percentage  = before_resolution_percentage
        bpy.context.scene.render.use_stamp_date         = before_use_stamp_date
        bpy.context.scene.render.use_stamp_time         = before_use_stamp_time
        bpy.context.scene.render.use_stamp_render_time  = before_use_stamp_render_time
        bpy.context.scene.render.use_stamp_frame        = before_use_stamp_frame
        bpy.context.scene.render.use_stamp_frame_range  = before_use_stamp_frame_range
        bpy.context.scene.render.use_stamp_memory       = before_use_stamp_memory
        bpy.context.scene.render.use_stamp_hostname     = before_use_stamp_hostname
        bpy.context.scene.render.use_stamp_camera       = before_use_stamp_camera
        bpy.context.scene.render.use_stamp_lens         = before_use_stamp_lens
        bpy.context.scene.render.use_stamp_scene        = before_use_stamp_scene
        bpy.context.scene.render.use_stamp_marker       = before_use_stamp_marker
        bpy.context.scene.render.use_stamp_filename     = before_use_stamp_filename
        bpy.context.scene.render.use_stamp_sequencer_strip = before_use_stamp_sequencer_strip
        bpy.context.scene.render.use_stamp_note         = before_use_stamp_note
        bpy.context.scene.render.use_stamp              = before_use_stamp
        bpy.context.scene.render.stamp_note_text        = before_stamp_note_text
        bpy.context.space_data.overlay.show_overlays    = before_show_overlays
        
        bpy.ops.render.play_rendered_anim()
                
        bpy.ops.screen.frame_jump(end=False)
        
        bpy.context.scene.render.image_settings.file_format = before_image_settings_file_format
        bpy.context.scene.render.filepath           = before_render_filepath
        bpy.context.scene.render.use_overwrite      = before_render_use_overwrite
        bpy.context.scene.render.use_file_extension = before_use_file_extension
        bpy.context.scene.render.ffmpeg.format      = before_output_encoding
        
class ViewPlayblast(Operator):
    bl_idname = "my.playblast_play"
    bl_label  = "View Playblast"
    bl_description="Play back rendered Playblast using an external player"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        before_render_filepath    = bpy.context.scene.render.filepath
        before_use_file_extension = bpy.context.scene.render.use_file_extension
        before_image_settings_file_format = bpy.context.scene.render.image_settings.file_format
        before_output_encoding    = bpy.context.scene.render.ffmpeg.format
        before_audio_codec        = bpy.context.scene.render.ffmpeg.audio_codec
        
        

        bpy.context.scene.render.use_file_extension = True  
        
        if bpy.types.Scene.saveOutputToFile:
            bpy.context.scene.render.filepath = bpy.types.Scene.output_file_path
            if len(bpy.types.Scene.output_file_name) > 0:
                bpy.context.scene.render.filepath += bpy.types.Scene.output_file_name + "_"
              
            # Video Settings          
            if bpy.types.Scene.isVideoFile:
                bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
                bpy.context.scene.render.ffmpeg.format = bpy.types.Scene.output_encoding
            else:
                bpy.context.scene.render.image_settings.file_format = bpy.types.Scene.image_file_format
            
            bpy.context.scene.render.ffmpeg.audio_codec = bpy.types.Scene.audio_codec
        else:
            bpy.context.scene.render.filepath = default_file_path
            bpy.context.scene.render.image_settings.file_format = 'PNG'
        
        bpy.ops.render.play_rendered_anim()
                       
        bpy.context.scene.render.image_settings.file_format = before_image_settings_file_format
        bpy.context.scene.render.filepath = before_render_filepath
        bpy.context.scene.render.use_file_extension = before_use_file_extension
        bpy.context.scene.render.ffmpeg.format = before_output_encoding
        bpy.context.scene.render.ffmpeg.audio_codec = before_audio_codec
        
        return {'FINISHED'}    
   
class PlayblastMainPanel(bpy.types.Panel):    
    bl_label = "Playblast"
    bl_category = "Playblast"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    
    def draw(self, context):
        split = self.layout.split()
        col = split.column(align = True)
        col.scale_y = 1.5
        col.operator("my.playblast", text = "PLAYBLAST", icon = "PLAY")
        
        split = self.layout.split()
        col = split.column(align = True)
        col.scale_y = 1.5
        col.operator("my.playblast_play", text = "VIEW(LAST)", icon = "RENDER_ANIMATION")
        
        split = self.layout.split()
        col = split.column(align = True)
        col.scale_y = 1.5
        col.operator("my.playblast_settings", text = "SETTING", icon = "MODIFIER_DATA")

def menu_func(self, context):
    self.layout.operator(Playblast.bl_idname)
    self.layout.operator(ViewPlayblast.bl_idname)
    self.layout.operator(PlayblastSettings.bl_idname)

classes = (
    Playblast,
    ViewPlayblast,
    PlayblastSettings,
    PlayblastMainPanel
)

def register():    
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
   
if __name__ == "__main__":
    register()
    

