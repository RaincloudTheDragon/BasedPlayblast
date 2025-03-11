bl_info = {
    "name": "BasedPlayblast",
    "author": "RaincloudTheDragon",
    "version": (0, 1, 1),
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
import shutil
import tempfile
from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty,
                       EnumProperty, PointerProperty)
from bpy.types import (Panel, Operator, AddonPreferences, PropertyGroup)

# Helper function to get file extension based on video format
def get_file_extension(video_format):
    if video_format == 'MPEG4':
        return ".mp4"
    elif video_format == 'QUICKTIME':
        return ".mov"
    elif video_format == 'AVI':
        return ".avi"
    elif video_format == 'MKV':
        return ".mkv"
    else:
        return ".mp4"  # Default to mp4 if unknown

# Function to get all cameras in the scene for the dropdown
def get_cameras(self, context):
    cameras = []
    for obj in context.scene.objects:
        if obj.type == 'CAMERA':
            cameras.append((obj.name, obj.name, f"Use camera: {obj.name}"))
    
    if not cameras:
        cameras.append(("NONE", "No Cameras", "No cameras in scene"))
    
    return cameras

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
    
    # Store the last created playblast file path
    last_playblast_file: StringProperty(
        name="Last Playblast File",
        description="Path to the last created playblast file",
        default=""
    )
    
    camera_object: EnumProperty(
        name="Camera",
        description="Camera to use for playblast",
        items=get_cameras
    )
    
    use_active_camera: BoolProperty(
        name="Use Scene Camera",
        description="Use the scene's active camera",
        default=True
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
            ('MPEG4', "MP4", "Standard container format with wide compatibility"),
            ('QUICKTIME', "QuickTime (MOV)", "Professional container format"),
            ('AVI', "AVI", "Classic container format"),
            ('MKV', "Matroska (MKV)", "Open source container with wide codec support")
        ],
        default='MPEG4'
    )
    
    video_codec: EnumProperty(
        name="Video Codec",
        description="Codec for video file",
        items=[
            ('H264', "H.264", "Standard codec with good quality and compression (recommended)"),
            ('NONE', "None", "No video codec")
        ],
        default='H264'
    )
    
    video_quality: EnumProperty(
        name="Quality",
        description="Quality of the video",
        items=[
            ('LOWEST', "Lowest", "Lowest quality"),
            ('VERYLOW', "Very Low", "Very low quality"),
            ('LOW', "Low", "Low quality"),
            ('MEDIUM', "Medium", "Medium quality"),
            ('HIGH', "High", "High quality"),
            ('PERC_LOSSLESS', "Perceptually Lossless", "Perceptually lossless quality"),
            ('LOSSLESS', "Lossless", "Lossless quality")
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
        default='SOLID'
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
    
    use_custom_ffmpeg_args: BoolProperty(
        name="Use Custom FFmpeg Args",
        description="Enable custom FFmpeg command line arguments for advanced users",
        default=False
    )
    
    custom_ffmpeg_args: StringProperty(
        name="Custom FFmpeg Args",
        description="Custom FFmpeg command line arguments (for advanced users)",
        default="-preset medium -crf 23"
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
        original_camera = scene.camera
        
        # Store original stamp settings
        original_use_stamp = scene.render.use_stamp
        if original_use_stamp:
            original_stamp_note_text = scene.render.stamp_note_text
            original_stamp_font_size = scene.render.stamp_font_size
            # Store other stamp settings as needed
        
        # Store original viewport settings
        space = None
        original_shading = None
        original_overlays = None
        original_view_perspective = None
        original_use_local_camera = None
        original_region_3d = None
        
        # Find a 3D view
        area = None
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                space = a.spaces.active
                original_shading = space.shading.type
                original_overlays = space.overlay.show_overlays
                
                # Store view settings
                for region in area.regions:
                    if region.type == 'WINDOW':
                        original_region_3d = region.data
                        if original_region_3d:
                            original_view_perspective = original_region_3d.view_perspective
                            if hasattr(original_region_3d, 'use_local_camera'):
                                original_use_local_camera = original_region_3d.use_local_camera
                        break
                break
        
        if not area:
            self.report({'ERROR'}, "No 3D viewport found")
            return {'CANCELLED'}
        
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
            
            # Set output path - ensure it has no file extension as Blender will add it
            file_name = props.file_name
            # Remove any existing extension if present
            if '.' in file_name:
                file_name = os.path.splitext(file_name)[0]
            scene.render.filepath = os.path.join(output_dir, file_name)
            
            # Set file format
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.format = props.video_format
            scene.render.ffmpeg.codec = props.video_codec
            
            # Apply quality settings (custom FFmpeg args will be handled separately)
            scene.render.ffmpeg.constant_rate_factor = props.video_quality
            
            # Audio settings
            if props.include_audio:
                scene.render.ffmpeg.audio_codec = props.audio_codec
                scene.render.ffmpeg.audio_bitrate = props.audio_bitrate
            else:
                scene.render.ffmpeg.audio_codec = 'NONE'
            
            # If using custom FFmpeg args, we'll need to run ffmpeg manually after the OpenGL render
            use_custom_args = props.use_custom_ffmpeg_args and props.custom_ffmpeg_args
            
            # Set camera if specified
            if not props.use_active_camera and props.camera_object != "NONE":
                camera_obj = context.scene.objects.get(props.camera_object)
                if camera_obj and camera_obj.type == 'CAMERA':
                    scene.camera = camera_obj
            
            # Override to ensure we're using the 3D view we found
            override = context.copy()
            override["area"] = area
            override["region"] = [r for r in area.regions if r.type == 'WINDOW'][0]
            
            # Set viewport display mode
            if space:
                # Force a redraw to ensure settings are applied
                context.view_layer.update()
                
                # Set shading type according to display_mode
                if space.shading.type != props.display_mode:
                    space.shading.type = props.display_mode
                    
                # Set overlay visibility
                if props.auto_disable_overlays and space.overlay.show_overlays:
                    space.overlay.show_overlays = False
                
                # Switch to camera view
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region_3d = region.data
                        if region_3d:
                            if region_3d.view_perspective != 'CAMERA':
                                region_3d.view_perspective = 'CAMERA'
                            if hasattr(region_3d, 'use_local_camera'):
                                region_3d.use_local_camera = False
                        break
                
                # Force another redraw to ensure camera view is active
                context.view_layer.update()
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # Add metadata if enabled
            if props.show_metadata:
                scene.render.use_stamp = True
                scene.render.use_stamp_date = props.metadata_date
                scene.render.use_stamp_time = props.metadata_date  # Use same setting as date
                scene.render.use_stamp_frame = props.metadata_frame
                scene.render.use_stamp_scene = props.metadata_scene
                scene.render.use_stamp_camera = props.metadata_camera
                scene.render.use_stamp_lens = props.metadata_lens
                
                # Set note text if provided
                if props.metadata_note:
                    scene.render.use_stamp_note = True
                    scene.render.stamp_note_text = props.metadata_note
                
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
            
            # Render the animation using the override context
            with context.temp_override(**override):
                bpy.ops.render.opengl(animation=True, sequencer=False, write_still=False, view_context=True)
            
            # Get the file extension
            file_ext = get_file_extension(props.video_format)
            
            # Find the actual output file
            import glob
            all_files = glob.glob(os.path.join(output_dir, "*" + file_ext))
            if all_files:
                # Get the most recently modified file
                latest_file = max(all_files, key=os.path.getmtime)
                self.report({'INFO'}, f"Playblast saved as: {os.path.basename(latest_file)}")
                # Store the path for the view_playblast operator
                props.last_playblast_file = latest_file
                
                # If using custom FFmpeg args, run ffmpeg manually
                if use_custom_args:
                    try:
                        import subprocess
                        import tempfile
                        
                        # Create a temporary file for the output
                        temp_output = os.path.join(tempfile.gettempdir(), f"custom_ffmpeg_output{file_ext}")
                        
                        # Build the ffmpeg command
                        ffmpeg_cmd = ["ffmpeg", "-y", "-i", latest_file]
                        # Add the custom args
                        ffmpeg_cmd.extend(props.custom_ffmpeg_args.split())
                        # Add the output file
                        ffmpeg_cmd.append(temp_output)
                        
                        # Run ffmpeg
                        self.report({'INFO'}, f"Running custom FFmpeg command: {' '.join(ffmpeg_cmd)}")
                        subprocess.run(ffmpeg_cmd, check=True)
                        
                        # Replace the original file with the processed one
                        import shutil
                        shutil.move(temp_output, latest_file)
                        
                        self.report({'INFO'}, f"Custom FFmpeg processing completed successfully")
                    except Exception as e:
                        self.report({'ERROR'}, f"Error processing with custom FFmpeg args: {str(e)}")
            else:
                self.report({'INFO'}, f"Playblast saved to {output_dir}")
                props.last_playblast_file = ""
            
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
            scene.camera = original_camera
            
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
            if space:
                space.shading.type = original_shading
                space.overlay.show_overlays = original_overlays
                
                # Restore view settings
                if original_region_3d:
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            region_3d = region.data
                            if region_3d:
                                region_3d.view_perspective = original_view_perspective
                                if hasattr(region_3d, 'use_local_camera') and original_use_local_camera is not None:
                                    region_3d.use_local_camera = original_use_local_camera
                            break
        
        # Play the animation immediately after creating it - just like in the original script
        if props.last_playblast_file:
            # Report which file we're playing
            self.report({'INFO'}, f"Opening playblast externally: {os.path.basename(props.last_playblast_file)}")
            
            # Open the file with the default system application
            try:
                if sys.platform == 'win32':
                    os.startfile(props.last_playblast_file)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(('open', props.last_playblast_file))
                else:  # Linux and other Unix-like
                    subprocess.call(('xdg-open', props.last_playblast_file))
            except Exception as e:
                self.report({'ERROR'}, f"Failed to open playblast: {str(e)}")
        
        return {'FINISHED'}

# View Playblast Operator
class BPL_OT_view_playblast(Operator):
    bl_idname = "bpl.view_playblast"
    bl_label = "View Playblast"
    bl_description = "Play back rendered Playblast"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        # Check if we have a playblast file
        if not props.last_playblast_file or not os.path.exists(props.last_playblast_file):
            self.report({'ERROR'}, "No playblast file found")
            return {'CANCELLED'}
        
        # Get the file path
        filepath = props.last_playblast_file
        
        # Report which file we're playing
        self.report({'INFO'}, f"Opening playblast externally: {os.path.basename(filepath)}")
        
        # Open the file with the default system application
        try:
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(('open', filepath))
            else:  # Linux and other Unix-like
                subprocess.call(('xdg-open', filepath))
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open playblast: {str(e)}")
            return {'CANCELLED'}

# View Latest Playblast Operator
class BPL_OT_view_latest_playblast(Operator):
    bl_idname = "bpl.view_latest_playblast"
    bl_label = "View Latest"
    bl_description = "Play back the most recent playblast"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        # Try to find the latest file in temp directory first
        temp_dir = os.path.join(tempfile.gettempdir(), "basedplayblast")
        latest_filepath = None
        
        # Check all possible video formats
        for format_name in ['MPEG4', 'QUICKTIME', 'AVI', 'MKV']:
            file_ext = get_file_extension(format_name)
            latest_filename = os.path.join(temp_dir, f"blast_latest{file_ext}")
            
            if os.path.exists(latest_filename):
                latest_filepath = latest_filename
                break
        
        # If no latest file found, try the last playblast file
        if not latest_filepath and props.last_playblast_file and os.path.exists(props.last_playblast_file):
            latest_filepath = props.last_playblast_file
        
        if not latest_filepath:
            self.report({'ERROR'}, "No recent playblast found")
            return {'CANCELLED'}
        
        # Report which file we're playing
        self.report({'INFO'}, f"Opening playblast externally: {os.path.basename(latest_filepath)}")
        
        # Open the file with the default system application
        try:
            if sys.platform == 'win32':
                os.startfile(latest_filepath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(('open', latest_filepath))
            else:  # Linux and other Unix-like
                subprocess.call(('xdg-open', latest_filepath))
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to open playblast: {str(e)}")
            return {'CANCELLED'}

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
        
        # Clear the last playblast file paths since we're changing the output path
        scene.basedplayblast.last_playblast_file = ""
        
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
        
        # Remove frame number pattern if present
        if '#' in file_name:
            file_name = file_name.split('#')[0]
        
        # Remove extension if present
        file_name = os.path.splitext(file_name)[0]
        
        # If file_name is empty, use a default
        if not file_name:
            file_name = "plyblst_"
        else:
            # Add the plyblst_ prefix if it's not already there
            if not file_name.startswith("plyblst_"):
                file_name = "plyblst_" + file_name
        
        # Set the BasedPlayblast file name
        scene.basedplayblast.file_name = file_name
        
        # Clear the last playblast file paths since we're changing the filename
        scene.basedplayblast.last_playblast_file = ""
        
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
        
        # Main buttons - now integrated with output settings
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("bpl.create_playblast", text="PLAYBLAST", icon='RENDER_ANIMATION')
        row.operator("bpl.view_playblast", text="VIEW", icon='PLAY')
        
        # Output settings - always visible
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
        
        # Camera settings - collapsible
        cam_box = layout.box()
        row = cam_box.row()
        row.prop(context.scene, "basedplayblast_show_camera", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_camera", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Camera")
        
        if context.scene.get("basedplayblast_show_camera", False):
            cam_box.prop(props, "use_active_camera")
            if not props.use_active_camera:
                cam_box.prop(props, "camera_object")
        
        # Resolution settings - collapsible
        res_box = layout.box()
        row = res_box.row()
        row.prop(context.scene, "basedplayblast_show_resolution", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_resolution", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Resolution")
        
        if context.scene.get("basedplayblast_show_resolution", False):
            res_box.prop(props, "resolution_mode")
            
            if props.resolution_mode == 'PRESET':
                res_box.prop(props, "resolution_preset")
            elif props.resolution_mode == 'CUSTOM':
                row = res_box.row()
                row.prop(props, "resolution_x")
                row.prop(props, "resolution_y")
            
            res_box.prop(props, "resolution_percentage")
        
        # Frame range - collapsible
        frame_box = layout.box()
        row = frame_box.row()
        row.prop(context.scene, "basedplayblast_show_frame_range", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_frame_range", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Frame Range")
        
        if context.scene.get("basedplayblast_show_frame_range", False):
            frame_box.prop(props, "use_scene_frame_range")
            
            if not props.use_scene_frame_range:
                row = frame_box.row()
                row.prop(props, "start_frame")
                row.prop(props, "end_frame")
        
        # File format - collapsible
        format_box = layout.box()
        row = format_box.row()
        row.prop(context.scene, "basedplayblast_show_format", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_format", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Format")
        
        if context.scene.get("basedplayblast_show_format", False):
            format_box.prop(props, "video_format")
            format_box.prop(props, "video_codec")
            
            # Custom FFmpeg arguments
            format_box.prop(props, "use_custom_ffmpeg_args")
            if props.use_custom_ffmpeg_args:
                format_box.prop(props, "custom_ffmpeg_args")
            else:
                format_box.prop(props, "video_quality")
            
            format_box.prop(props, "include_audio")
            if props.include_audio:
                format_box.prop(props, "audio_codec")
                format_box.prop(props, "audio_bitrate")
        
        # Display settings - collapsible
        display_box = layout.box()
        row = display_box.row()
        row.prop(context.scene, "basedplayblast_show_display", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_display", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Display")
        
        if context.scene.get("basedplayblast_show_display", False):
            display_box.prop(props, "display_mode")
            display_box.prop(props, "auto_disable_overlays")
        
        # Metadata - collapsible
        meta_box = layout.box()
        row = meta_box.row()
        row.prop(context.scene, "basedplayblast_show_metadata", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_metadata", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Metadata")
        
        if context.scene.get("basedplayblast_show_metadata", False):
            meta_box.prop(props, "show_metadata", text="Show Metadata")
            
            if props.show_metadata:
                meta_box.prop(props, "metadata_note")
                
                col = meta_box.column(align=True)
                row = col.row(align=True)
                row.prop(props, "metadata_date", toggle=True)
                row.prop(props, "metadata_frame", toggle=True)
                
                row = col.row(align=True)
                row.prop(props, "metadata_scene", toggle=True)
                row.prop(props, "metadata_camera", toggle=True)
                
                row = col.row(align=True)
                row.prop(props, "metadata_lens", toggle=True)
                row.prop(props, "metadata_resolution", toggle=True)

# Registration
classes = (
    BPLProperties,
    BPL_OT_create_playblast,
    BPL_OT_view_playblast,
    BPL_OT_view_latest_playblast,
    BPL_OT_sync_output_path,
    BPL_OT_sync_file_name,
    BPL_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.basedplayblast = PointerProperty(type=BPLProperties)
    
    # Register properties for collapsible sections
    bpy.types.Scene.basedplayblast_show_camera = BoolProperty(
        name="Show Camera Settings",
        default=False
    )
    bpy.types.Scene.basedplayblast_show_resolution = BoolProperty(
        name="Show Resolution Settings",
        default=False
    )
    bpy.types.Scene.basedplayblast_show_frame_range = BoolProperty(
        name="Show Frame Range Settings",
        default=False
    )
    bpy.types.Scene.basedplayblast_show_format = BoolProperty(
        name="Show Format Settings",
        default=False
    )
    bpy.types.Scene.basedplayblast_show_display = BoolProperty(
        name="Show Display Settings",
        default=False
    )
    bpy.types.Scene.basedplayblast_show_metadata = BoolProperty(
        name="Show Metadata Settings",
        default=False
    )

def unregister():
    # Unregister properties for collapsible sections
    del bpy.types.Scene.basedplayblast_show_camera
    del bpy.types.Scene.basedplayblast_show_resolution
    del bpy.types.Scene.basedplayblast_show_frame_range
    del bpy.types.Scene.basedplayblast_show_format
    del bpy.types.Scene.basedplayblast_show_display
    del bpy.types.Scene.basedplayblast_show_metadata
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.basedplayblast

if __name__ == "__main__":
    register()