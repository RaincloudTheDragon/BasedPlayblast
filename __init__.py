bl_info = {
    "name": "BasedPlayblast",
    "author": "RaincloudTheDragon",
    "version": (0, 1, 0),
    "blender": (4, 3, 2),
    "location": "Properties > Output > BasedPlayblast",
    "description": "Create high-quality playblasts from Blender",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}

import bpy
import os
import subprocess
import sys
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty,
                       EnumProperty, PointerProperty)
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)

# Main Properties class
class BPLProperties(PropertyGroup):
    output_path: StringProperty(
        name="Output Path",
        description="Path to save the playblast",
        default="//playblast/",
        subtype='DIR_PATH'
    )
    
    file_name: StringProperty(
        name="File Name",
        description="Base name for the playblast files",
        default="plyblst_"
    )
    
    resolution_mode: EnumProperty(
        name="Resolution Mode",
        description="How to determine the resolution",
        items=[
            ('SCENE', "Use Scene Resolution", "Use the scene's render resolution"),
            ('PRESET', "Preset Resolution", "Use a preset resolution"),
            ('CUSTOM', "Custom Resolution", "Use a custom resolution")
        ],
        default='SCENE'
    )
    
    resolution_preset: EnumProperty(
        name="Resolution Preset",
        description="Common resolution presets",
        items=[
            ('x1920y1080', "1920 x 1080 (16:9) HD1080p", ""),
            ('x1280y720', "1280 x 720 (16:9) HD720p", ""),
            ('x854y480', "854 x 480 (16:9) 480P", ""),
            ('x640y360', "640 x 360 (16:9) 360P", ""),
            ('x1920y1440', "1920 x 1440 (4:3)", ""),
            ('x1600y1200', "1600 x 1200 (4:3)", ""),
            ('x1280y960', "1280 x 960 (4:3)", ""),
            ('x1024y768', "1024 x 768 (4:3)", ""),
            ('x800y600', "800 x 600 (4:3)", ""),
            ('x640y480', "640 x 480 (4:3)", ""),
            ('x1024y1024', "1024 x 1024 (1:1)", ""),
            ('x512y512', "512 x 512 (1:1)", "")
        ],
        default='x1920y1080'
    )
    
    resolution_x: IntProperty(
        name="Resolution X",
        description="Width of the playblast",
        default=1920,
        min=4
    )
    
    resolution_y: IntProperty(
        name="Resolution Y",
        description="Height of the playblast",
        default=1080,
        min=4
    )
    
    resolution_percentage: IntProperty(
        name="Resolution %",
        description="Percentage of the resolution",
        default=100,
        min=1,
        max=100,
        subtype='PERCENTAGE'
    )
    
    use_scene_frame_range: BoolProperty(
        name="Use Scene Frame Range",
        description="Use the scene's frame range for the playblast",
        default=True
    )
    
    start_frame: IntProperty(
        name="Start Frame",
        description="First frame to playblast",
        default=1
    )
    
    end_frame: IntProperty(
        name="End Frame",
        description="Last frame to playblast",
        default=250
    )
    
    file_format: EnumProperty(
        name="File Format",
        description="Format to save the playblast",
        items=[
            ('VIDEO', "Video File", "Save as video file")
        ],
        default='VIDEO'
    )
    
    video_format: EnumProperty(
        name="Video Format",
        description="Format for video file",
        items=[
            ('MPEG4', "MPEG-4 (MP4)", "Save as MP4 file (widely compatible)"),
            ('QUICKTIME', "QuickTime (MOV)", "Save as QuickTime file"),
            ('AVI', "AVI", "Save as AVI file"),
            ('MKV', "Matroska (MKV)", "Save as MKV file")
        ],
        default='MPEG4'
    )
    
    video_codec: EnumProperty(
        name="Video Codec",
        description="Codec for video file",
        items=[
            ('H264', "H.264", "H.264 codec"),
            ('MPEG4', "MPEG-4", "MPEG-4 codec"),
            ('HUFFYUV', "HuffYUV", "HuffYUV codec"),
            ('NONE', "None", "No video codec")
        ],
        default='H264'
    )
    
    video_quality: EnumProperty(
        name="Quality",
        description="Quality of the video",
        items=[
            ('LOWEST', "Lowest", "Lowest quality"),
            ('LOW', "Low", "Low quality"),
            ('MEDIUM', "Medium", "Medium quality"),
            ('HIGH', "High", "High quality"),
            ('HIGHEST', "Highest", "Highest quality")
        ],
        default='MEDIUM'
    )
    
    include_audio: BoolProperty(
        name="Include Audio",
        description="Include audio in the playblast",
        default=False
    )
    
    audio_codec: EnumProperty(
        name="Audio Codec",
        description="Codec for audio",
        items=[
            ('AAC', "AAC", "AAC codec"),
            ('AC3', "AC3", "AC3 codec"),
            ('MP3', "MP3", "MP3 codec"),
            ('NONE', "None", "No audio codec")
        ],
        default='AAC'
    )
    
    audio_bitrate: IntProperty(
        name="Audio Bitrate",
        description="Bitrate for audio (kb/s)",
        default=192,
        min=32,
        max=384
    )
    
    display_mode: EnumProperty(
        name="Display Mode",
        description="How to display the viewport",
        items=[
            ('WIREFRAME', "Wireframe", "Display the wireframe"),
            ('SOLID', "Solid", "Display solid shading"),
            ('MATERIAL', "Material", "Display material preview"),
            ('RENDERED', "Rendered", "Display rendered preview")
        ],
        default='MATERIAL'
    )
    
    auto_disable_overlays: BoolProperty(
        name="Auto Disable Overlays",
        description="Automatically disable viewport overlays during playblast",
        default=True
    )
    
    show_metadata: BoolProperty(
        name="Show Metadata",
        description="Show metadata in the playblast",
        default=True
    )
    
    metadata_resolution: BoolProperty(
        name="Resolution",
        description="Show resolution in metadata",
        default=True
    )
    
    metadata_frame: BoolProperty(
        name="Frame",
        description="Show frame number in metadata",
        default=True
    )
    
    metadata_scene: BoolProperty(
        name="Scene",
        description="Show scene name in metadata",
        default=True
    )
    
    metadata_camera: BoolProperty(
        name="Camera",
        description="Show camera name in metadata",
        default=True
    )
    
    metadata_lens: BoolProperty(
        name="Lens",
        description="Show camera lens in metadata",
        default=True
    )
    
    metadata_date: BoolProperty(
        name="Date",
        description="Show date in metadata",
        default=True
    )
    
    metadata_note: StringProperty(
        name="Note",
        description="Custom note to include in metadata",
        default=""
    )

# Main Operator
class BPL_OT_create_playblast(Operator):
    bl_idname = "bpl.create_playblast"
    bl_label = "Create Playblast"
    bl_description = "Create a playblast of the current scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        # Store original render settings
        original_path = scene.render.filepath
        original_x = scene.render.resolution_x
        original_y = scene.render.resolution_y
        original_percentage = scene.render.resolution_percentage
        original_file_format = scene.render.image_settings.file_format
        original_color_mode = scene.render.image_settings.color_mode
        original_use_file_extension = scene.render.use_file_extension
        original_use_overwrite = scene.render.use_overwrite
        original_use_placeholder = scene.render.use_placeholder
        original_frame_start = scene.frame_start
        original_frame_end = scene.frame_end
        
        # Store original stamp settings
        original_use_stamp = scene.render.use_stamp
        if original_use_stamp:
            original_stamp_note_text = scene.render.stamp_note_text
            original_stamp_font_size = scene.render.stamp_font_size
            # Store other stamp settings as needed
        
        # Store original viewport settings
        space = context.space_data
        if space and space.type == 'VIEW_3D':
            original_shading = space.shading.type
            original_overlays = space.overlay.show_overlays
        else:
            # Find a 3D view
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    space = area.spaces.active
                    original_shading = space.shading.type
                    original_overlays = space.overlay.show_overlays
                    break
        
        try:
            # Set resolution based on mode
            if props.resolution_mode == 'SCENE':
                # Use scene resolution
                pass  # We'll keep the scene's resolution
            elif props.resolution_mode == 'PRESET':
                # Parse the preset string to get resolution
                preset = props.resolution_preset
                x_str = preset.split('y')[0].replace('x', '')
                y_str = preset.split('y')[1]
                scene.render.resolution_x = int(x_str)
                scene.render.resolution_y = int(y_str)
            else:  # CUSTOM
                scene.render.resolution_x = props.resolution_x
                scene.render.resolution_y = props.resolution_y
            
            # Set resolution percentage
            scene.render.resolution_percentage = props.resolution_percentage
            
            # Set frame range
            if props.use_scene_frame_range:
                start_frame = scene.frame_start
                end_frame = scene.frame_end
            else:
                # Temporarily change scene frame range
                scene.frame_start = props.start_frame
                scene.frame_end = props.end_frame
                start_frame = props.start_frame
                end_frame = props.end_frame
            
            # Create output directory if it doesn't exist
            output_dir = bpy.path.abspath(props.output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Set output path
            scene.render.filepath = os.path.join(output_dir, props.file_name)
            
            # Set file format
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.format = props.video_format
            scene.render.ffmpeg.codec = props.video_codec
            scene.render.ffmpeg.constant_rate_factor = props.video_quality
            
            # Audio settings
            if props.include_audio:
                scene.render.ffmpeg.audio_codec = props.audio_codec
                scene.render.ffmpeg.audio_bitrate = props.audio_bitrate
            else:
                scene.render.ffmpeg.audio_codec = 'NONE'
            
            # Set viewport display mode
            if space and space.type == 'VIEW_3D':
                space.shading.type = props.display_mode
                if props.auto_disable_overlays:
                    space.overlay.show_overlays = False
            
            # Add metadata if enabled
            if props.show_metadata:
                scene.render.use_stamp = True
                scene.render.stamp_note_text = props.metadata_note
                scene.render.stamp_font_size = 12
                
                # Set which metadata to show - use try/except for each in case they're read-only
                try:
                    scene.render.use_stamp_time = False
                except:
                    pass
                
                try:
                    scene.render.use_stamp_date = props.metadata_date
                except:
                    pass
                
                try:
                    scene.render.use_stamp_render_time = False
                except:
                    pass
                
                try:
                    scene.render.use_stamp_frame = props.metadata_frame
                except:
                    pass
                
                try:
                    scene.render.use_stamp_scene = props.metadata_scene
                except:
                    pass
                
                try:
                    scene.render.use_stamp_camera = props.metadata_camera
                except:
                    pass
                
                try:
                    scene.render.use_stamp_lens = props.metadata_lens
                except:
                    pass
                
                try:
                    scene.render.use_stamp_filename = False
                except:
                    pass
                
                try:
                    scene.render.use_stamp_marker = False
                except:
                    pass
                
                try:
                    scene.render.use_stamp_sequencer_strip = False
                except:
                    pass
                
                if props.metadata_resolution:
                    res_x = scene.render.resolution_x * scene.render.resolution_percentage // 100
                    res_y = scene.render.resolution_y * scene.render.resolution_percentage // 100
                    try:
                        scene.render.stamp_note_text += f" | {res_x}x{res_y}"
                    except:
                        pass
            else:
                scene.render.use_stamp = False
            
            # Render the animation (not frame by frame)
            bpy.ops.render.opengl(animation=True)
            
            self.report({'INFO'}, f"Playblast saved to {output_dir}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating playblast: {str(e)}")
            return {'CANCELLED'}
        
        finally:
            # Restore original settings
            scene.render.filepath = original_path
            scene.render.resolution_x = original_x
            scene.render.resolution_y = original_y
            scene.render.resolution_percentage = original_percentage
            scene.render.image_settings.file_format = original_file_format
            scene.render.image_settings.color_mode = original_color_mode
            scene.render.use_file_extension = original_use_file_extension
            scene.render.use_overwrite = original_use_overwrite
            scene.render.use_placeholder = original_use_placeholder
            
            # Restore stamp settings
            scene.render.use_stamp = original_use_stamp
            if original_use_stamp:
                try:
                    scene.render.stamp_note_text = original_stamp_note_text
                    scene.render.stamp_font_size = original_stamp_font_size
                    # Restore other stamp settings as needed
                except:
                    pass
            
            # Restore frame range if we changed it
            if not props.use_scene_frame_range:
                scene.frame_start = original_frame_start
                scene.frame_end = original_frame_end
            
            # Restore viewport settings
            if space and space.type == 'VIEW_3D':
                space.shading.type = original_shading
                space.overlay.show_overlays = original_overlays
        
        return {'FINISHED'}

# View Playblast Operator
class BPL_OT_view_playblast(Operator):
    bl_idname = "bpl.view_playblast"
    bl_label = "View Playblast"
    bl_description = "Open the playblast in the default viewer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        output_dir = bpy.path.abspath(props.output_path)
        
        # Determine the file extension based on video format
        if props.video_format == 'MPEG4':
            file_ext = ".mp4"
        elif props.video_format == 'QUICKTIME':
            file_ext = ".mov"
        elif props.video_format == 'AVI':
            file_ext = ".avi"
        elif props.video_format == 'MKV':
            file_ext = ".mkv"
        else:
            file_ext = ".mp4"  # Default to mp4 if unknown
        
        # Construct the filepath
        filepath = os.path.join(output_dir, props.file_name + file_ext)
        
        # Check if the file exists
        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"File not found: {filepath}")
            return {'CANCELLED'}
        
        # Open the file with the default application
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':
            subprocess.call(['open', filepath])
        else:
            subprocess.call(['xdg-open', filepath])
        
        return {'FINISHED'}

# Operator to sync output path with Blender's render output path
class BPL_OT_sync_output_path(Operator):
    bl_idname = "bpl.sync_output_path"
    bl_label = "Sync Output Path"
    bl_description = "Use Blender's render output path"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        # Get Blender's render output path
        blender_output_path = bpy.path.abspath(scene.render.filepath)
        
        # If it's a file path, extract the directory
        if os.path.isfile(blender_output_path) or '.' in os.path.basename(blender_output_path):
            blender_output_path = os.path.dirname(blender_output_path)
        
        # Ensure it ends with a separator
        if not blender_output_path.endswith(os.sep):
            blender_output_path += os.sep
        
        # Set the BasedPlayblast output path
        scene.basedplayblast.output_path = blender_output_path
        
        self.report({'INFO'}, f"Output path synced with Blender's render output path")
        return {'FINISHED'}

# Operator to sync file name with Blender's output file name
class BPL_OT_sync_file_name(Operator):
    bl_idname = "bpl.sync_file_name"
    bl_label = "Sync File Name"
    bl_description = "Use Blender's output file name"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        # Get Blender's render output path
        blender_output_path = bpy.path.abspath(scene.render.filepath)
        
        # Extract the file name without extension
        file_name = os.path.basename(blender_output_path)
        
        # Remove frame number pattern and extension if present
        file_name = file_name.split('#')[0].split('.')[0]
        
        # If file_name is empty, use a default
        if not file_name:
            file_name = "plyblst_"
        else:
            # Add the plyblst_ prefix if it's not already there
            if not file_name.startswith("plyblst_"):
                file_name = "plyblst_" + file_name
        
        # Set the BasedPlayblast file name
        scene.basedplayblast.file_name = file_name
        
        self.report({'INFO'}, f"File name synced with Blender's output file name")
        return {'FINISHED'}

# UI Panel
class BPL_PT_main_panel(Panel):
    bl_label = "BasedPlayblast"
    bl_idname = "BPL_PT_main_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1  # This positions it right after the main Output panel (which has bl_order=0)
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.basedplayblast
        
        # Output settings
        box = layout.box()
        box.label(text="Output Settings")
        
        # Output path with sync button
        row = box.row(align=True)
        row.prop(props, "output_path")
        row.operator("bpl.sync_output_path", text="", icon='FILE_REFRESH')
        
        # File name with sync button
        row = box.row(align=True)
        row.prop(props, "file_name")
        row.operator("bpl.sync_file_name", text="", icon='FILE_REFRESH')
        
        # Resolution settings
        box = layout.box()
        box.label(text="Resolution")
        box.prop(props, "resolution_mode")
        
        if props.resolution_mode == 'PRESET':
            box.prop(props, "resolution_preset")
        elif props.resolution_mode == 'CUSTOM':
            row = box.row()
            row.prop(props, "resolution_x")
            row.prop(props, "resolution_y")
        
        box.prop(props, "resolution_percentage")
        
        # Frame range
        box = layout.box()
        box.label(text="Frame Range")
        box.prop(props, "use_scene_frame_range")
        
        if not props.use_scene_frame_range:
            row = box.row()
            row.prop(props, "start_frame")
            row.prop(props, "end_frame")
        
        # File format
        box = layout.box()
        box.label(text="Format")
        box.prop(props, "video_format")
        box.prop(props, "video_codec")
        box.prop(props, "video_quality")
        
        box.prop(props, "include_audio")
        if props.include_audio:
            box.prop(props, "audio_codec")
            box.prop(props, "audio_bitrate")
        
        # Display settings
        box = layout.box()
        box.label(text="Display")
        box.prop(props, "display_mode")
        box.prop(props, "auto_disable_overlays")
        
        # Metadata
        box = layout.box()
        box.prop(props, "show_metadata", text="Show Metadata")
        
        if props.show_metadata:
            col = box.column(align=True)
            row = col.row()
            row.prop(props, "metadata_resolution", text="Resolution")
            row.prop(props, "metadata_frame", text="Frame")
            
            row = col.row()
            row.prop(props, "metadata_scene", text="Scene")
            row.prop(props, "metadata_date", text="Date")
            
            row = col.row()
            row.prop(props, "metadata_camera", text="Camera")
            row.prop(props, "metadata_lens", text="Lens")
            
            box.prop(props, "metadata_note")
        
        # Operators
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("bpl.create_playblast", icon='RENDER_ANIMATION')
        row.operator("bpl.view_playblast", icon='PLAY')

# Registration
classes = (
    BPLProperties,
    BPL_OT_create_playblast,
    BPL_OT_view_playblast,
    BPL_OT_sync_output_path,
    BPL_OT_sync_file_name,
    BPL_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.basedplayblast = PointerProperty(type=BPLProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.basedplayblast

if __name__ == "__main__":
    register()