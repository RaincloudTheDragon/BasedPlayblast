bl_info = {
    "name": "BasedPlayblast",
    "author": "RaincloudTheDragon",
    "version": (0, 3, 1),
    "blender": (4, 3, 0),
    "location": "Properties > Output > BasedPlayblast",
    "description": "Easily create playblasts from Blender",
    "warning": "",
    "doc_url": "https://github.com/RaincloudTheDragon/BasedPlayblast",
    "category": "Animation",
}

import bpy # type: ignore
import os
import subprocess
import sys
import tempfile
import glob  # Add missing import
from bpy.props import (StringProperty, BoolProperty, IntProperty, EnumProperty, PointerProperty, FloatProperty) # type: ignore
from bpy.types import (Panel, Operator, PropertyGroup, AddonPreferences) # type: ignore
import time

# Import the updater module
from . import addon_updater_ops

# Pre-defined items lists for EnumProperties
RESOLUTION_MODE_ITEMS = [
    ('SCENE', "Use Scene Resolution", "Use the scene's render resolution"),
    ('PRESET', "Preset Resolution", "Use a preset resolution"),
    ('CUSTOM', "Custom Resolution", "Use a custom resolution")
]

RESOLUTION_PRESET_ITEMS = [
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
]

FILE_FORMAT_ITEMS = [
    ('VIDEO', "Video File", "Save as video file")
]

VIDEO_FORMAT_ITEMS = [
    ('MPEG4', "MP4", "Standard container format with wide compatibility"),
    ('QUICKTIME', "QuickTime (MOV)", "Professional container format"),
    ('AVI', "AVI", "Classic container format"),
    ('MKV', "Matroska (MKV)", "Open source container with wide codec support")
]

VIDEO_CODEC_ITEMS = [
    ('H264', "H.264", "Standard codec with good quality and compression (recommended)"),
    ('NONE', "None", "No video codec")
]

VIDEO_QUALITY_ITEMS = [
    ('LOWEST', "Lowest", "Lowest quality"),
    ('VERYLOW', "Very Low", "Very low quality"),
    ('LOW', "Low", "Low quality"),
    ('MEDIUM', "Medium", "Medium quality"),
    ('HIGH', "High", "High quality"),
    ('PERC_LOSSLESS', "Perceptually Lossless", "Perceptually lossless quality"),
    ('LOSSLESS', "Lossless", "Lossless quality")
]

AUDIO_CODEC_ITEMS = [
    ('AAC', "AAC", "AAC codec"),
    ('AC3', "AC3", "AC3 codec"),
    ('MP3', "MP3", "MP3 codec"),
    ('NONE', "None", "No audio codec")
]

DISPLAY_MODE_ITEMS = [
    ('WIREFRAME', "Wireframe", "Display the wireframe"),
    ('SOLID', "Solid", "Display solid shading"),
    ('MATERIAL', "Material", "Display material preview"),
    ('RENDERED', "Rendered", "Display rendered preview")
]

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
def get_cameras(self, context) -> list[tuple[str, str, str]]:
    cameras = []
    for obj in context.scene.objects:
        if obj.type == 'CAMERA':
            cameras.append((obj.name, obj.name, f"Use camera: {obj.name}"))
    
    if not cameras:
        cameras.append(("NONE", "No Cameras", "No cameras in scene"))
    
    return cameras

# Main Properties class
class BPLProperties(PropertyGroup):
    output_path: StringProperty(  # type: ignore
        name="Output Path",
        description="Path to save the playblast",
        default="//blast/",
        subtype='DIR_PATH'
    )
    
    file_name: StringProperty(  # type: ignore
        name="File Name",
        description="Base name for the playblast files",
        default="blast_"
    )
    
    last_playblast_file: StringProperty(  # type: ignore
        name="Last Playblast File",
        description="Path to the last created playblast file",
        default=""
    )
    
    camera_object: EnumProperty(  # type: ignore
        name="Camera",
        description="Camera to use for playblast",
        items=get_cameras
    )
    
    use_active_camera: BoolProperty(  # type: ignore
        name="Use Scene Camera",
        description="Use the scene's active camera",
        default=True
    )
    
    resolution_mode: EnumProperty(  # type: ignore
        name="Resolution Mode",
        description="How to determine the resolution",
        items=RESOLUTION_MODE_ITEMS,
        default='SCENE'
    )
    
    resolution_preset: EnumProperty(  # type: ignore
        name="Resolution Preset",
        description="Common resolution presets",
        items=RESOLUTION_PRESET_ITEMS,
        default='x1920y1080'
    )
    
    resolution_x: IntProperty(  # type: ignore
        name="Resolution X",
        description="Width of the playblast",
        default=1920,
        min=4
    )
    
    resolution_y: IntProperty(  # type: ignore
        name="Resolution Y",
        description="Height of the playblast",
        default=1080,
        min=4
    )
    
    resolution_percentage: IntProperty(  # type: ignore
        name="Resolution %",
        description="Percentage of the resolution",
        default=100,
        min=1,
        max=100,
        subtype='PERCENTAGE'
    )
    
    use_scene_frame_range: BoolProperty(  # type: ignore
        name="Use Scene Frame Range",
        description="Use the scene's frame range for the playblast",
        default=True
    )
    
    start_frame: IntProperty(  # type: ignore
        name="Start Frame",
        description="First frame to playblast",
        default=1
    )
    
    end_frame: IntProperty(  # type: ignore
        name="End Frame",
        description="Last frame to playblast",
        default=250
    )
    
    file_format: EnumProperty(  # type: ignore
        name="File Format",
        description="Format to save the playblast",
        items=FILE_FORMAT_ITEMS,
        default='VIDEO'
    )
    
    video_format: EnumProperty(  # type: ignore
        name="Video Format",
        description="Format for video file",
        items=VIDEO_FORMAT_ITEMS,
        default='MPEG4'
    )
    
    video_codec: EnumProperty(  # type: ignore
        name="Video Codec",
        description="Codec for video file",
        items=VIDEO_CODEC_ITEMS,
        default='H264'
    )
    
    video_quality: EnumProperty(  # type: ignore
        name="Quality",
        description="Quality of the video",
        items=VIDEO_QUALITY_ITEMS,
        default='MEDIUM'
    )
    
    include_audio: BoolProperty(  # type: ignore
        name="Include Audio",
        description="Include audio in the playblast",
        default=False
    )
    
    audio_codec: EnumProperty(  # type: ignore
        name="Audio Codec",
        description="Codec for audio",
        items=AUDIO_CODEC_ITEMS,
        default='AAC'
    )
    
    audio_bitrate: IntProperty(  # type: ignore
        name="Audio Bitrate",
        description="Bitrate for audio (kb/s)",
        default=192,
        min=32,
        max=384
    )
    
    display_mode: EnumProperty(  # type: ignore
        name="Display Mode",
        description="How to display the viewport",
        items=DISPLAY_MODE_ITEMS,
        default='SOLID'
    )
    
    auto_disable_overlays: BoolProperty(  # type: ignore
        name="Auto Disable Overlays",
        description="Automatically disable viewport overlays during playblast",
        default=True
    )
    
    show_metadata: BoolProperty(  # type: ignore
        name="Show Metadata",
        description="Show metadata in the playblast",
        default=True
    )
    
    metadata_resolution: BoolProperty(  # type: ignore
        name="Resolution",
        description="Show resolution in metadata",
        default=True
    )
    
    metadata_frame: BoolProperty(  # type: ignore
        name="Frame",
        description="Show frame number in metadata",
        default=True
    )
    
    metadata_scene: BoolProperty(  # type: ignore
        name="Scene",
        description="Show scene name in metadata",
        default=True
    )
    
    metadata_camera: BoolProperty(  # type: ignore
        name="Camera",
        description="Show camera name in metadata",
        default=True
    )
    
    metadata_lens: BoolProperty(  # type: ignore
        name="Lens",
        description="Show camera lens in metadata",
        default=True
    )
    
    metadata_date: BoolProperty(  # type: ignore
        name="Date",
        description="Show date in metadata",
        default=True
    )
    
    metadata_note: StringProperty(  # type: ignore
        name="Note",
        description="Custom note to include in metadata",
        default=""
    )
    
    use_custom_ffmpeg_args: BoolProperty(  # type: ignore
        name="Use Custom FFmpeg Args",
        description="Enable custom FFmpeg command line arguments for advanced users",
        default=False
    )
    
    custom_ffmpeg_args: StringProperty(  # type: ignore
        name="Custom FFmpeg Args",
        description="Custom FFmpeg command line arguments (for advanced users)",
        default="-preset medium -crf 23"
    )
    
    is_rendering: BoolProperty(  # type: ignore
        name="Is Rendering",
        default=False
    )
    
    render_progress: FloatProperty(  # type: ignore
        name="Render Progress",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    
    status_message: StringProperty(  # type: ignore
        name="Status Message",
        default=""
    )
    
    # Add the property to store original settings at scene level
    original_settings: StringProperty(  # type: ignore
        name="Original Settings",
        description="JSON string holding original render settings",
        default=""
    )
    
    # Add property to store extended settings like light states
    original_settings_extended: StringProperty(  # type: ignore
        name="Extended Original Settings",
        description="String holding additional original settings like light states",
        default=""
    )

# Main Operator
class BPL_OT_create_playblast(Operator):
    bl_idname = "bpl.create_playblast"
    bl_label = "Create Playblast"
    bl_description = "Create a playblast of the current scene"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    
    _timer = None
    _area = None
    _space = None
    _region_3d = None
    _original_settings = None
    _original_shading = None
    _original_overlays = None
    _original_view_perspective = None
    _original_use_local_camera = None
    _phase = 'SETUP'  # SETUP, RENDER, ENCODE, COMPLETE
    _last_reported_frame = 0
    _frame_start = 0
    _frame_end = 0
    _current_frame = 0
    
    def modal(self, context, event):
        if event.type == 'ESC':
            context.window_manager.event_timer_remove(self._timer)
            bpy.ops.render.render('INVOKE_DEFAULT', animation=False)  # This cancels the render
            self.cleanup(context)
            return {'CANCELLED'}
        
        if event.type == 'TIMER':
            props = context.scene.basedplayblast
            
            if self._phase == 'SETUP':
                props.render_progress = 0.0
                props.status_message = "Setting up playblast..."
                props.is_rendering = True
                self._phase = 'RENDER'
                
                # Start the render
                override = context.copy()
                override["area"] = self._area
                override["region"] = [r for r in self._area.regions if r.type == 'WINDOW'][0]
                with context.temp_override(**override):
                    bpy.ops.render.opengl('INVOKE_DEFAULT', animation=True, sequencer=False, write_still=False, view_context=True)
                
                # Force redraw of UI
                for area in context.screen.areas:
                    if area.type == 'PROPERTIES':
                        area.tag_redraw()
                
                return {'PASS_THROUGH'}
            
            elif self._phase == 'RENDER':
                # Get current frame and calculate progress
                current_frame = context.scene.frame_current
                
                # Check if frame has changed since last time
                if current_frame != self._last_reported_frame:
                    self._last_reported_frame = current_frame
                    total_frames = self._frame_end - self._frame_start + 1
                    
                    # Calculate progress based on current frame
                    if current_frame >= self._frame_start:
                        frame_progress = current_frame - self._frame_start
                        progress = min((frame_progress / total_frames) * 100, 100)
                        
                        # Update properties
                        props.render_progress = progress
                        props.status_message = f"Rendering frame {current_frame}/{self._frame_end} ({int(progress)}%)"
                        print(f"Progress update: frame {current_frame}, progress {int(progress)}%")
                        
                        # Force UI redraw
                        for area in context.screen.areas:
                            if area.type == 'PROPERTIES':
                                area.tag_redraw()
                
                # Force all 3D viewports to update
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                
                # Check if output file exists and has expected size to determine completion
                file_ext = get_file_extension(context.scene.basedplayblast.video_format)
                output_path = bpy.path.abspath(context.scene.render.filepath)
                full_path = output_path + file_ext
                
                # When playhead loops back to first frame after rendering all frames
                # or if the output file exists and seems complete, consider rendering done
                if (current_frame == self._frame_start and self._last_reported_frame >= self._frame_end) or os.path.exists(full_path):
                    # If we've seen the last frame or the file exists, consider it done
                    print(f"Detected playblast completion - Output file exists: {os.path.exists(full_path)}")
                    
                    self._phase = 'COMPLETE'
                    props.render_progress = 100.0
                    props.status_message = "Finalizing output..."
                    
                    # Force UI redraw
                    for area in context.screen.areas:
                        if area.type == 'PROPERTIES':
                            area.tag_redraw()
                
                # Also check direct frame count for completion (look for final frame minus one)
                elif current_frame >= (self._frame_end - 1):
                    # Force frame to end+1 to ensure render completion is detected
                    context.scene.frame_set(self._frame_end)
                    
                    self._phase = 'COMPLETE'
                    props.render_progress = 100.0
                    props.status_message = "Finalizing output..."
                    
                    # Force UI redraw
                    for area in context.screen.areas:
                        if area.type == 'PROPERTIES':
                            area.tag_redraw()
            
            elif self._phase == 'COMPLETE':
                props.render_progress = 0.0
                props.status_message = ""
                props.is_rendering = False
                context.window_manager.event_timer_remove(self._timer)
                self.finish(context)
                
                # Force UI redraw
                for area in context.screen.areas:
                    if area.type == 'PROPERTIES':
                        area.tag_redraw()
                
                return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        scene = context.scene
        props = scene.basedplayblast
        
        # Initialize phase
        self._phase = 'SETUP'
        self._last_reported_frame = 0
        
        # Store frame range
        self._frame_start = scene.frame_start if props.use_scene_frame_range else props.start_frame
        self._frame_end = scene.frame_end if props.use_scene_frame_range else props.end_frame
        self._current_frame = scene.frame_current
        
        # Temporarily override Blender's frame range if using manual range
        original_frame_start = scene.frame_start
        original_frame_end = scene.frame_end
        if not props.use_scene_frame_range:
            scene.frame_start = props.start_frame
            scene.frame_end = props.end_frame
            print(f"Using manual frame range: {props.start_frame} - {props.end_frame}")
        
        # Store original settings
        self._original_settings = {
            'filepath': scene.render.filepath,
            'resolution_x': scene.render.resolution_x,
            'resolution_y': scene.render.resolution_y,
            'resolution_percentage': scene.render.resolution_percentage,
            'use_file_extension': scene.render.use_file_extension,
            'use_overwrite': scene.render.use_overwrite,
            'use_placeholder': scene.render.use_placeholder,
            'camera': scene.camera,
            'frame_start': original_frame_start,  # Store original frame start
            'frame_end': original_frame_end,      # Store original frame end
            'image_settings': {
                'file_format': scene.render.image_settings.file_format,
                'color_mode': scene.render.image_settings.color_mode
            },
            'display_mode': context.preferences.view.render_display_type,
            # Store metadata settings
            'use_stamp': scene.render.use_stamp,
            'use_stamp_date': scene.render.use_stamp_date,
            'use_stamp_time': scene.render.use_stamp_time,
            'use_stamp_frame': scene.render.use_stamp_frame,
            'use_stamp_camera': scene.render.use_stamp_camera,
            'use_stamp_lens': scene.render.use_stamp_lens,
            'use_stamp_scene': scene.render.use_stamp_scene,
            'use_stamp_note': scene.render.use_stamp_note,
            'stamp_note_text': scene.render.stamp_note_text
        }
        
        # Set render display type to NONE to hide render window
        context.preferences.view.render_display_type = 'NONE'
        
        # Find a 3D view
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                self._area = a
                self._space = a.spaces.active
                for region in a.regions:
                    if region.type == 'WINDOW':
                        region_3d = region.data
                        if region_3d:
                            self._region_3d = region_3d
                            self._original_view_perspective = region_3d.view_perspective
                            if hasattr(region_3d, 'use_local_camera'):
                                self._original_use_local_camera = region_3d.use_local_camera
                        break
                break
        
        if not self._area or not self._space:
            self.report({'ERROR'}, "No 3D viewport found")
            return {'CANCELLED'}
        
        # Store viewport settings
        self._original_shading = self._space.shading.type
        self._original_overlays = self._space.overlay.show_overlays
        
        try:
            # Set resolution based on mode
            if props.resolution_mode == 'PRESET':
                preset = props.resolution_preset
                x_str = preset.split('y')[0].replace('x', '')
                y_str = preset.split('y')[1]
                scene.render.resolution_x = int(x_str)
                scene.render.resolution_y = int(y_str)
            elif props.resolution_mode == 'CUSTOM':
                scene.render.resolution_x = props.resolution_x
                scene.render.resolution_y = props.resolution_y
            
            scene.render.resolution_percentage = props.resolution_percentage
            
            # Create output directory
            output_dir = bpy.path.abspath(props.output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Set output path
            file_name = props.file_name
            if '.' in file_name:
                file_name = os.path.splitext(file_name)[0]
            scene.render.filepath = os.path.join(output_dir, file_name)
            
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
            
            # Set camera if specified
            if not props.use_active_camera and props.camera_object != "NONE":
                camera_obj = context.scene.objects.get(props.camera_object)
                if camera_obj and camera_obj.type == 'CAMERA':
                    scene.camera = camera_obj
            
            # Setup metadata
            if props.show_metadata:
                scene.render.use_stamp = True
                scene.render.use_stamp_date = props.metadata_date
                scene.render.use_stamp_time = props.metadata_date  # Usually linked with date
                scene.render.use_stamp_frame = props.metadata_frame
                scene.render.use_stamp_camera = props.metadata_camera
                scene.render.use_stamp_lens = props.metadata_lens
                scene.render.use_stamp_scene = props.metadata_scene
                
                # Set note if provided
                if props.metadata_note:
                    scene.render.use_stamp_note = True
                    
                    # Build the note text
                    note = props.metadata_note
                    
                    # Add resolution info if enabled
                    if props.metadata_resolution:
                        res_x = scene.render.resolution_x * (scene.render.resolution_percentage / 100.0)
                        res_y = scene.render.resolution_y * (scene.render.resolution_percentage / 100.0)
                        note += f"\nResolution: {int(res_x)} x {int(res_y)}"
                    
                    scene.render.stamp_note_text = note
            else:
                scene.render.use_stamp = False
            
            # Set viewport display mode
            if self._space:
                # Set shading type according to display_mode
                if self._space.shading.type != props.display_mode:
                    self._space.shading.type = props.display_mode
                    
                # Set overlay visibility
                if props.auto_disable_overlays:
                    self._space.overlay.show_overlays = False
                
                # Switch to camera view if needed
                if self._region_3d and self._region_3d.view_perspective != 'CAMERA':
                    self._region_3d.view_perspective = 'CAMERA'
                    if hasattr(self._region_3d, 'use_local_camera'):
                        self._region_3d.use_local_camera = False
            
            # Create override context
            override = context.copy()
            override["area"] = self._area
            override["region"] = [r for r in self._area.regions if r.type == 'WINDOW'][0]
            
            # Start progress bar
            context.window_manager.progress_begin(0, 1.0)
            
            # Add timer for modal - update every 0.1 seconds for more frequent updates
            self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
            context.window_manager.modal_handler_add(self)
            
            return {'RUNNING_MODAL'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating playblast: {str(e)}")
            self.cleanup(context)
            return {'CANCELLED'}        

    def finish(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        # Find and open the output file
        file_ext = get_file_extension(props.video_format)
        output_dir = bpy.path.abspath(props.output_path)
        all_files = glob.glob(os.path.join(output_dir, "*" + file_ext))
        if all_files:
            latest_file = max(all_files, key=os.path.getmtime)
            props.last_playblast_file = latest_file
            
            try:
                if sys.platform == 'win32':
                    os.startfile(latest_file)
                elif sys.platform == 'darwin':
                    subprocess.call(('open', latest_file))
                else:
                    subprocess.call(('xdg-open', latest_file))
            except Exception as e:
                self.report({'ERROR'}, f"Failed to open playblast: {str(e)}")    

        self.cleanup(context)
    
    def cleanup(self, context):
        # Reset progress properties
        props = context.scene.basedplayblast
        props.is_rendering = False
        props.render_progress = 0.0
        props.status_message = ""
        
        # End progress bar if it's still running
        context.window_manager.progress_end()
        
        # Remove timer if it exists
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
        
        # Restore viewport settings
        if self._space:
            self._space.shading.type = self._original_shading
            self._space.overlay.show_overlays = self._original_overlays
            
            # Restore view settings
            if self._region_3d:
                if self._original_view_perspective:
                    self._region_3d.view_perspective = self._original_view_perspective
                if self._original_use_local_camera is not None:
                    self._region_3d.use_local_camera = self._original_use_local_camera
        
        # Restore render settings
        if self._original_settings:
            scene = context.scene
            scene.render.filepath = self._original_settings['filepath']
            scene.render.resolution_x = self._original_settings['resolution_x']
            scene.render.resolution_y = self._original_settings['resolution_y']
            scene.render.resolution_percentage = self._original_settings['resolution_percentage']
            scene.render.use_file_extension = self._original_settings['use_file_extension']
            scene.render.use_overwrite = self._original_settings['use_overwrite']
            scene.render.use_placeholder = self._original_settings['use_placeholder']
            scene.camera = self._original_settings['camera']
            scene.render.image_settings.file_format = self._original_settings['image_settings']['file_format']
            scene.render.image_settings.color_mode = self._original_settings['image_settings']['color_mode']
            context.preferences.view.render_display_type = self._original_settings['display_mode']
            
            # Restore frame range to original values
            scene.frame_start = self._original_settings['frame_start']
            scene.frame_end = self._original_settings['frame_end']
            
            # Restore metadata settings
            scene.render.use_stamp = self._original_settings['use_stamp']
            scene.render.use_stamp_date = self._original_settings['use_stamp_date']
            scene.render.use_stamp_time = self._original_settings['use_stamp_time']
            scene.render.use_stamp_frame = self._original_settings['use_stamp_frame']
            scene.render.use_stamp_camera = self._original_settings['use_stamp_camera']
            scene.render.use_stamp_lens = self._original_settings['use_stamp_lens']
            scene.render.use_stamp_scene = self._original_settings['use_stamp_scene']
            scene.render.use_stamp_note = self._original_settings['use_stamp_note']
            scene.render.stamp_note_text = self._original_settings['stamp_note_text']
        
        # Force a redraw to ensure viewport updates
        for area in context.screen.areas:
            area.tag_redraw()

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
            file_name = "blast_"
        else:
            # Add the blast_ prefix if it's not already there
            if not file_name.startswith("blast_"):
                file_name = "blast_" + file_name
        
        # Set the BasedPlayblast file name
        scene.basedplayblast.file_name = file_name
        
        # Clear the last playblast file paths since we're changing the filename
        scene.basedplayblast.last_playblast_file = ""
        
        self.report({'INFO'}, f"File name synced with Blender's output file name")
        return {'FINISHED'}

# New operator to apply blast render settings
class BPL_OT_apply_blast_settings(Operator):
    bl_idname = "bpl.apply_blast_settings"
    bl_label = "Apply Blast Render Settings"
    bl_description = "Apply Playblast render settings to the scene without rendering"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # We need os, sys and json in this scope where they're used
        import os
        
        scene = context.scene
        props = scene.basedplayblast
        
        # First, save the original settings if not already saved
        if not props.original_settings:
            import json
            original_settings = {
                'filepath': scene.render.filepath,
                'resolution_x': scene.render.resolution_x,
                'resolution_y': scene.render.resolution_y,
                'resolution_percentage': scene.render.resolution_percentage,
                'use_file_extension': scene.render.use_file_extension,
                'use_overwrite': scene.render.use_overwrite,
                'use_placeholder': scene.render.use_placeholder,
                'camera': scene.camera.name if scene.camera else "",
                'frame_start': scene.frame_start,
                'frame_end': scene.frame_end,
                'image_settings': {
                    'file_format': scene.render.image_settings.file_format,
                    'color_mode': scene.render.image_settings.color_mode
                },
                'display_mode': context.preferences.view.render_display_type,
                # Store render engine
                'render_engine': scene.render.engine,
                # Store world
                'world': scene.world.name if scene.world else "",
                # Store metadata settings
                'use_stamp': scene.render.use_stamp,
                'use_stamp_date': scene.render.use_stamp_date,
                'use_stamp_time': scene.render.use_stamp_time,
                'use_stamp_frame': scene.render.use_stamp_frame,
                'use_stamp_camera': scene.render.use_stamp_camera,
                'use_stamp_lens': scene.render.use_stamp_lens,
                'use_stamp_scene': scene.render.use_stamp_scene,
                'use_stamp_note': scene.render.use_stamp_note,
                'stamp_note_text': scene.render.stamp_note_text
            }
            props.original_settings = json.dumps(original_settings)
        
        # Find a 3D view to apply shading settings
        found_3d_view = False
        for a in context.screen.areas:
            if a.type == 'VIEW_3D':
                space = a.spaces.active
                original_shading = space.shading.type
                original_overlays = space.overlay.show_overlays
                
                # Set shading type according to display_mode
                space.shading.type = props.display_mode
                    
                # Set overlay visibility
                if props.auto_disable_overlays:
                    space.overlay.show_overlays = False
                
                # For camera view, find the 3D region
                for region in a.regions:
                    if region.type == 'WINDOW':
                        region_3d = space.region_3d
                        if region_3d:
                            # Store and set view
                            original_view_perspective = region_3d.view_perspective
                            original_use_local_camera = getattr(region_3d, 'use_local_camera', None)
                            
                            # Switch to camera view if needed
                            region_3d.view_perspective = 'CAMERA'
                            if hasattr(region_3d, 'use_local_camera'):
                                region_3d.use_local_camera = False
                        break
                
                found_3d_view = True
                break
        
        if not found_3d_view:
            self.report({'WARNING'}, "No 3D viewport found to apply display settings")
        
        try:
            # Set render engine based on display mode - this is the critical addition!
            if props.display_mode == 'RENDERED':
                # For rendered preview, we'll optimize the render settings 
                # while keeping the scene's chosen render engine
                try:
                    # Store current render engine to report later
                    current_engine = scene.render.engine
                    print(f"Using existing render engine: {current_engine}")
                    
                    # Apply engine-specific optimizations
                    if current_engine == 'BLENDER_EEVEE' or current_engine == 'BLENDER_EEVEE_NEXT':
                        # Apply EEVEE-specific optimizations for faster rendering
                        eevee_attr = 'eevee' if hasattr(scene, 'eevee') else 'eevee_next'
                        eevee = getattr(scene, eevee_attr) if hasattr(scene, eevee_attr) else None
                        
                        if eevee:
                            # Set minimal acceptable quality
                            if hasattr(eevee, 'taa_render_samples'):
                                eevee.taa_render_samples = 4  # Balance between quality and speed for final render
                                print(f"Set render samples to 4 for RENDERED mode")
                            
                            # Minimal shadow settings - but keep shadows for realism
                            if hasattr(eevee, 'shadow_cube_size'):
                                eevee.shadow_cube_size = '512'  # Medium shadow resolution
                            if hasattr(eevee, 'use_soft_shadows'):
                                eevee.use_soft_shadows = True  # Keep soft shadows for realism
                            
                            # Disable expensive effects
                            if hasattr(eevee, 'use_bloom'):
                                eevee.use_bloom = False
                            if hasattr(eevee, 'use_ssr'):
                                eevee.use_ssr = False
                            if hasattr(eevee, 'use_motion_blur'):
                                eevee.use_motion_blur = False
                            if hasattr(eevee, 'use_volumetric_lights'):
                                eevee.use_volumetric_lights = False
                            
                            # Use moderate global illumination
                            if hasattr(eevee, 'gi_diffuse_bounces'):
                                eevee.gi_diffuse_bounces = 1  # Just one bounce for indirect lighting
                                
                            # Enable persistent data if available for faster animation rendering
                            if hasattr(eevee, 'use_persistent_data'):
                                eevee.use_persistent_data = True
                                print(f"Enabled persistent data for faster EEVEE animation rendering")
                                
                            print(f"Applied optimized EEVEE settings for RENDERED mode")
                            
                    elif current_engine == 'CYCLES':
                        # Apply Cycles-specific optimizations
                        cycles = scene.cycles
                        
                        # Use extremely low samples for preview
                        if hasattr(cycles, 'samples'):
                            cycles.samples = 8  # Absolute minimum for playblast
                            print(f"Set Cycles samples to 8 for maximum speed")
                        
                        # Disable denoising entirely for faster rendering
                        if hasattr(cycles, 'use_denoising'):
                            cycles.use_denoising = False
                            print(f"Disabled Cycles denoising for maximum speed")
                        
                        # Use fastest render settings
                        if hasattr(cycles, 'max_bounces'):
                            cycles.max_bounces = 2  # Almost no light bounces
                        if hasattr(cycles, 'diffuse_bounces'):
                            cycles.diffuse_bounces = 1  # Minimal diffuse
                        if hasattr(cycles, 'glossy_bounces'):
                            cycles.glossy_bounces = 1  # Minimal reflections
                        if hasattr(cycles, 'transmission_bounces'):
                            cycles.transmission_bounces = 1  # Minimal glass/transparency
                        if hasattr(cycles, 'volume_bounces'):
                            cycles.volume_bounces = 0  # No volume scattering
                        if hasattr(cycles, 'caustics_reflective'):
                            cycles.caustics_reflective = False  # Disable reflective caustics
                        if hasattr(cycles, 'caustics_refractive'):
                            cycles.caustics_refractive = False  # Disable refractive caustics
                        
                        # Set pixel filter width to 0.01 for faster rendering
                        if hasattr(cycles, 'pixel_filter_width'):
                            cycles.pixel_filter_width = 0.01
                            
                        # Use lowest quality shadow and AO settings
                        if hasattr(cycles, 'ao_bounces'):
                            cycles.ao_bounces = 1
                        if hasattr(cycles, 'ao_bounces_render'):
                            cycles.ao_bounces_render = 1
                            
                        # Use adaptive sampling with very low thresholds
                        if hasattr(cycles, 'use_adaptive_sampling'):
                            cycles.use_adaptive_sampling = True
                        if hasattr(cycles, 'adaptive_threshold'):
                            cycles.adaptive_threshold = 0.5  # Very high threshold = faster convergence
                        if hasattr(cycles, 'adaptive_min_samples'):
                            cycles.adaptive_min_samples = 0  # Allow adaptive sampling to stop early
                            
                        # Use faster integrator settings
                        if hasattr(cycles, 'light_sampling_threshold'):
                            cycles.light_sampling_threshold = 0.5
                            
                        # CRITICAL: Enable persistent data for much faster animation rendering
                        if hasattr(cycles, 'use_persistent_data'):
                            cycles.use_persistent_data = True
                            print(f"Enabled persistent data for faster animation rendering")
                            
                        # Use faster GPU rendering if available
                        if hasattr(cycles, 'device'):
                            # Try to use GPU if available
                            try:
                                cycles.device = 'GPU'
                            except:
                                # If setting GPU fails, stick with current device
                                pass
                                
                        print(f"Applied optimized Cycles settings for RENDERED mode")
                    
                    # General optimizations regardless of render engine
                    
                    # Enable simplify settings for render
                    if hasattr(scene.render, 'use_simplify'):
                        scene.render.use_simplify = True
                        
                        # Set moderate simplification for final render
                        if hasattr(scene.render, 'simplify_subdivision'):
                            scene.render.simplify_subdivision = 1
                        if hasattr(scene.render, 'simplify_child_particles'):
                            scene.render.simplify_child_particles = 0.5
                        if hasattr(scene.render, 'simplify_volumes'):
                            scene.render.simplify_volumes = 0.5
                            
                    # Disable compositor for faster rendering
                    scene.use_nodes = False
                    
                    # Reduce texture size limit for faster material evaluation
                    if hasattr(scene.render, 'texture_limit'):
                        scene.render.texture_limit = '2048'  # Reduced but still decent quality
                    
                    # Disable motion blur
                    if hasattr(scene.render, 'use_motion_blur'):
                        scene.render.use_motion_blur = False
                        
                    # Keep all lights and world settings for RENDERED mode
                    # This is the key difference from MATERIAL mode - we want to use
                    # the actual scene lighting and world settings
                    
                    print(f"RENDERED preview mode configured with optimized settings")
                
                except Exception as e:
                    self.report({'WARNING'}, f"Note: Couldn't set all RENDERED mode settings: {str(e)}")
            elif props.display_mode == 'MATERIAL':
                # For material preview, use EEVEE 
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
                
                # Material preview uses an HDRI environment for lighting
                try:
                    # Completely remove scene world - critical for studio lighting
                    scene.world = None
                    
                    # CRITICAL FIX: Store and temporarily disable all scene lights
                    original_light_states = {}
                    for obj in scene.objects:
                        if obj.type == 'LIGHT':
                            # Store original visibility and hide status
                            original_light_states[obj.name] = {
                                'hide_viewport': obj.hide_viewport,
                                'hide_render': obj.hide_render,
                                'visible_camera': obj.visible_camera,
                                'visible_diffuse': obj.visible_diffuse,
                                'visible_glossy': obj.visible_glossy,
                                'visible_transmission': obj.visible_transmission,
                                'visible_volume_scatter': obj.visible_volume_scatter
                            }
                            
                            # Disable the light completely for rendering
                            obj.hide_render = True
                            obj.hide_viewport = True
                            obj.visible_camera = False
                            obj.visible_diffuse = False
                            obj.visible_glossy = False
                            obj.visible_transmission = False
                            obj.visible_volume_scatter = False
                            
                            print(f"Temporarily disabled light: {obj.name}")
                    
                    # Get path to Blender installation and construct studio lights path
                    # Make sure modules are available for this section
                    import os
                    import sys
                    
                    # Get the Blender executable path
                    blender_exe = bpy.app.binary_path
                    blender_dir = os.path.dirname(blender_exe)
                    
                    # Construct path to studio lights directory
                    # Note: This may vary based on Blender installation but should work for most setups
                    studio_lights_dir = os.path.join(blender_dir, "datafiles", "studiolights", "world")
                    
                    # Additional paths for different Blender installations (specifically for Blender 4.4)
                    possible_paths = [
                        # Standard path
                        studio_lights_dir,
                        # Blender 4.4 specific path structure with extra version directory
                        os.path.join(blender_dir, "4.4", "datafiles", "studiolights", "world"),
                        # Other possible locations
                        os.path.join(blender_dir, "..", "datafiles", "studiolights", "world"),
                        os.path.join(blender_dir, "..", "..", "datafiles", "studiolights", "world"),
                        os.path.join(blender_dir, "..", "4.4", "datafiles", "studiolights", "world"),
                        os.path.join(os.path.dirname(os.path.dirname(blender_exe)), "4.4", "datafiles", "studiolights", "world"),
                        # Version-specific paths for various Blender installations
                        os.path.join(os.path.dirname(blender_dir), "4.4", "datafiles", "studiolights", "world")
                    ]
                    
                    # Get Blender's version and construct a version-specific path
                    blender_version = bpy.app.version
                    version_str = f"{blender_version[0]}.{blender_version[1]}"
                    possible_paths.append(os.path.join(blender_dir, version_str, "datafiles", "studiolights", "world"))
                    possible_paths.append(os.path.join(os.path.dirname(blender_dir), version_str, "datafiles", "studiolights", "world"))
                    
                    # Specific path for this user's installation
                    possible_paths.append(r"C:\Program Files\Blender Foundation\Blender 4.4\4.4\datafiles\studiolights\world")
                    
                    # Try to find the studio lights directory
                    studio_lights_dir = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            print(f"Found studio lights directory: {path}")
                            studio_lights_dir = path
                            break
                    
                    if not studio_lights_dir:
                        print("Could not find studio lights directory, using fallback")
                        studio_lights_dir = possible_paths[0]  # Use the first path as fallback
                    
                    # Find the specific HDRI to use - these are common in Blender 4.4
                    common_hdri_files = [
                        "forest.exr",      # Forest environment - good general lighting (preferred)
                        "studio.exr",      # Clean studio environment
                        "city.exr",        # Urban environment
                        "courtyard.exr",   # Outdoor courtyard
                        "night.exr",       # Night environment
                        "sunrise.exr",     # Sunrise lighting
                        "sunset.exr",      # Sunset lighting
                    ]
                    
                    # Try to find an existing HDRI file
                    hdri_path = None
                    for hdri_filename in common_hdri_files:
                        path = os.path.join(studio_lights_dir, hdri_filename)
                        if os.path.exists(path):
                            hdri_path = path
                            print(f"Found HDRI file: {hdri_path}")
                            break
                    
                    # If no common HDRI was found, try any .exr file
                    if not hdri_path and os.path.exists(studio_lights_dir):
                        try:
                            exr_files = [f for f in os.listdir(studio_lights_dir) if f.endswith('.exr')]
                            if exr_files:
                                hdri_filename = exr_files[0]
                                hdri_path = os.path.join(studio_lights_dir, hdri_filename)
                                print(f"Using alternative HDRI: {hdri_path}")
                        except Exception as e:
                            print(f"Error listing studio lights directory: {str(e)}")
                    
                    # Hardcoded paths as last resort
                    if not hdri_path or not os.path.exists(hdri_path):
                        direct_paths = [
                            r"C:\Program Files\Blender Foundation\Blender 4.4\4.4\datafiles\studiolights\world\forest.exr",
                            r"C:\Program Files\Blender Foundation\Blender 4.4\4.4\datafiles\studiolights\world\studio.exr",
                            # Try both common locations
                            os.path.join(studio_lights_dir, "forest.exr"),
                            os.path.join(os.path.dirname(studio_lights_dir), "world", "forest.exr")
                        ]
                        for path in direct_paths:
                            if os.path.exists(path):
                                hdri_path = path
                                print(f"Using hardcoded HDRI path: {hdri_path}")
                                break
                    
                    if hdri_path and os.path.exists(hdri_path):
                        print(f"Using HDRI path: {hdri_path}")
                    else:
                        print("WARNING: Could not find any suitable HDRI file!")
                
                    # Create a new world to use for rendering
                    new_world = None
                    # First, check if we already have a world with this name
                    world_name = f"BasedPlayblast_StudioHDRI"
                    if world_name in bpy.data.worlds:
                        new_world = bpy.data.worlds[world_name]
                    else:
                        # Create a new world
                        new_world = bpy.data.worlds.new(world_name)
                    
                    # Setup world to use the HDRI
                    new_world.use_nodes = True
                    nodes = new_world.node_tree.nodes
                    
                    # Clear existing nodes
                    for node in nodes:
                        nodes.remove(node)
                    
                    # Create background and output nodes
                    background = nodes.new(type='ShaderNodeBackground')
                    output = nodes.new(type='ShaderNodeOutputWorld')
                    
                    # Set background strength for proper lighting intensity
                    if hasattr(background.inputs[1], 'default_value'):
                        background.inputs[1].default_value = 1.0  # Strength of 1.0 is standard for material preview
                    
                    # Set a default color for the background (light gray to provide some lighting)
                    if hasattr(background.inputs[0], 'default_value'):
                        background.inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)
                    
                    # Position nodes
                    background.location = (0, 0)
                    output.location = (300, 0)
                    
                    # Link nodes for basic background
                    links = new_world.node_tree.links
                    links.new(background.outputs["Background"], output.inputs["Surface"])
                    
                    # Only add the texture node if we have a valid HDRI
                    if hdri_path and os.path.exists(hdri_path):
                        # Create texture node
                        tex_node = nodes.new(type='ShaderNodeTexEnvironment')
                        tex_node.location = (-300, 0)
                        
                        # Load the HDRI file
                        try:
                            # Try to load the image with performance optimizations
                            image = bpy.data.images.load(hdri_path, check_existing=True)
                            tex_node.image = image
                            
                            # Optimize the image for rendering performance
                            if hasattr(image, 'colorspace_settings'):
                                # Use a proper linear colorspace from the available options
                                # "Linear" alone isn't valid in Blender 4.4
                                try:
                                    image.colorspace_settings.name = 'Linear Rec.709'  # Most common linear space
                                except:
                                    # If that fails, try a different linear option
                                    try:
                                        image.colorspace_settings.name = 'Linear ACES'
                                    except:
                                        # Just use the default - don't change it
                                        pass
                            
                            # Link the texture to background
                            links.new(tex_node.outputs["Color"], background.inputs["Color"])
                            print(f"Successfully loaded HDRI: {hdri_path}")
                        except Exception as e:
                            print(f"Error loading HDRI: {str(e)}")
                            print("Using default background color instead")
                    else:
                        print("No valid HDRI path found - using default background color")
                    
                    # Set the world for rendering
                    scene.world = new_world
                    
                    # Set the appropriate attribute for EEVEE settings
                    eevee_attr = 'eevee' if hasattr(scene, 'eevee') else 'eevee_next'
                    eevee = getattr(scene, eevee_attr) if hasattr(scene, eevee_attr) else None
                    
                    if eevee:
                        # For material preview, we need to use the environment rather than studio lights
                        if hasattr(eevee, 'use_scene_lights'):
                            eevee.use_scene_lights = False
                            print(f"Disabled scene lights for EEVEE render")
                        if hasattr(eevee, 'use_scene_world'):
                            # THIS IS IMPORTANT - we're using our own world node setup, not studio light
                            eevee.use_scene_world = True
                            print(f"Enabled scene world for EEVEE render")
                            
                        # Use minimum possible samples for fastest rendering
                        if hasattr(eevee, 'taa_render_samples'):
                            eevee.taa_render_samples = 4
                            print(f"Set render samples to 4")
                        
                        # Disable features not used in material preview
                        if hasattr(eevee, 'use_bloom'):
                            eevee.use_bloom = False
                        if hasattr(eevee, 'use_ssr'):
                            eevee.use_ssr = False
                        if hasattr(eevee, 'use_gtao'):
                            eevee.use_gtao = False
                        if hasattr(eevee, 'use_volumetric_lights'):
                            eevee.use_volumetric_lights = False
                        
                        # Disable global illumination
                        if hasattr(eevee, 'gi_diffuse_bounces'):
                            eevee.gi_diffuse_bounces = 0
                        
                        # Set additional minimum quality settings
                        if hasattr(eevee, 'shadow_cube_size'):
                            eevee.shadow_cube_size = '64'  # Minimum shadow resolution
                        if hasattr(eevee, 'shadow_cascade_size'):
                            eevee.shadow_cascade_size = '64'  # Minimum shadow resolution
                        if hasattr(eevee, 'use_soft_shadows'):
                            eevee.use_soft_shadows = False  # Disable soft shadows
                        if hasattr(eevee, 'sss_samples'):
                            eevee.sss_samples = 1  # Minimum subsurface scattering samples
                        if hasattr(eevee, 'volumetric_samples'):
                            eevee.volumetric_samples = 1  # Minimum volumetric samples
                            
                        # Additional performance optimizations
                        # Disable motion blur
                        if hasattr(eevee, 'use_motion_blur'):
                            eevee.use_motion_blur = False
                            
                        # Disable ambient occlusion (AO)
                        if hasattr(eevee, 'use_gtao'):
                            eevee.use_gtao = False
                            
                            # Disable screen space reflections entirely
                            if hasattr(eevee, 'use_ssr'):
                                eevee.use_ssr = False
                        
                        # Reduce texture size limit for faster material evaluation
                        if hasattr(scene.render, 'texture_limit'):
                            scene.render.texture_limit = '1024'
                            
                        # Enable simplify settings for render
                        if hasattr(scene.render, 'use_simplify'):
                            scene.render.use_simplify = True
                            
                            # Set maximum simplification
                            if hasattr(scene.render, 'simplify_subdivision'):
                                scene.render.simplify_subdivision = 0
                            if hasattr(scene.render, 'simplify_child_particles'):
                                scene.render.simplify_child_particles = 0
                            if hasattr(scene.render, 'simplify_volumes'):
                                scene.render.simplify_volumes = 0
                                
                        # Optimize compositor settings
                        scene.use_nodes = False  # Disable compositor nodes
                            
                        # Use smaller tile size for faster updating
                        if hasattr(eevee, 'tile_size'):
                            eevee.tile_size = '8'  # Use 8x8 tiles for faster rendering
                        
                        # Disable film transparency if not needed
                        if hasattr(scene.render, 'film_transparent'):
                            scene.render.film_transparent = False
                                            
                        # Ensure background is colored by the environment
                        background = new_world.node_tree.nodes.get('Background')
                        if background and hasattr(background.inputs[0], 'default_value'):
                            # Make sure the background node uses the HDRI color
                            pass  # Already properly set up in node setup
                            
                        print(f"All EEVEE settings set to minimum quality for fastest rendering")
                        
                        # Save original settings to restore later
                        props.original_settings_extended = str(original_light_states)
                    else:
                        self.report({'WARNING'}, f"Could not find EEVEE settings - material preview may not render correctly")
                
                except Exception as e:
                    self.report({'WARNING'}, f"Note: Couldn't set all EEVEE settings: {str(e)}")
            else:
                # For SOLID or WIREFRAME, use Workbench
                scene.render.engine = 'BLENDER_WORKBENCH'
                
                # Configure workbench settings based on current viewport
                if found_3d_view:
                    scene.display.shading.light = space.shading.light
                    scene.display.shading.color_type = space.shading.color_type
                    scene.display.shading.show_object_outline = space.shading.show_object_outline
                    if props.display_mode == 'WIREFRAME':
                        scene.display.shading.type = 'WIREFRAME'
                    else:
                        scene.display.shading.type = 'SOLID'
            
            # Set resolution based on mode
            if props.resolution_mode == 'PRESET':
                preset = props.resolution_preset
                x_str = preset.split('y')[0].replace('x', '')
                y_str = preset.split('y')[1]
                scene.render.resolution_x = int(x_str)
                scene.render.resolution_y = int(y_str)
            elif props.resolution_mode == 'CUSTOM':
                scene.render.resolution_x = props.resolution_x
                scene.render.resolution_y = props.resolution_y
            
            scene.render.resolution_percentage = props.resolution_percentage
            
            # Create output directory
            output_dir = bpy.path.abspath(props.output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Set output path
            file_name = props.file_name
            if '.' in file_name:
                file_name = os.path.splitext(file_name)[0]
            scene.render.filepath = os.path.join(output_dir, file_name)
            
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
            
            # Set camera if specified
            if not props.use_active_camera and props.camera_object != "NONE":
                camera_obj = context.scene.objects.get(props.camera_object)
                if camera_obj and camera_obj.type == 'CAMERA':
                    scene.camera = camera_obj
            
            # Set frame range if using manual range
            if not props.use_scene_frame_range:
                scene.frame_start = props.start_frame
                scene.frame_end = props.end_frame
            
            # Setup metadata
            if props.show_metadata:
                scene.render.use_stamp = True
                scene.render.use_stamp_date = props.metadata_date
                scene.render.use_stamp_time = props.metadata_date  # Usually linked with date
                scene.render.use_stamp_frame = props.metadata_frame
                scene.render.use_stamp_camera = props.metadata_camera
                scene.render.use_stamp_lens = props.metadata_lens
                scene.render.use_stamp_scene = props.metadata_scene
                
                # Set note if provided
                if props.metadata_note:
                    scene.render.use_stamp_note = True
                    
                    # Build the note text
                    note = props.metadata_note
                    
                    # Add resolution info if enabled
                    if props.metadata_resolution:
                        res_x = scene.render.resolution_x * (scene.render.resolution_percentage / 100.0)
                        res_y = scene.render.resolution_y * (scene.render.resolution_percentage / 100.0)
                        note += f"\nResolution: {int(res_x)} x {int(res_y)}"
                    
                    scene.render.stamp_note_text = note
            else:
                scene.render.use_stamp = False
            
            self.report({'INFO'}, f"Blast settings applied, render engine set to {scene.render.engine}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error applying settings: {str(e)}")
            return {'CANCELLED'}

# New operator to restore original render settings
class BPL_OT_restore_original_settings(Operator):
    bl_idname = "bpl.restore_original_settings"
    bl_label = "Restore Original Render Settings"
    bl_description = "Restore the original render settings before the blast settings were applied"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.basedplayblast
        
        # Check if we have original settings saved
        if not props.original_settings:
            self.report({'ERROR'}, "No original settings saved to restore")
            return {'CANCELLED'}
        
        try:
            import json
            import ast  # For evaluating the saved light states
            original = json.loads(props.original_settings)
            
            # Restore render settings
            scene.render.filepath = original['filepath']
            scene.render.resolution_x = original['resolution_x']
            scene.render.resolution_y = original['resolution_y']
            scene.render.resolution_percentage = original['resolution_percentage']
            scene.render.use_file_extension = original['use_file_extension']
            scene.render.use_overwrite = original['use_overwrite']
            scene.render.use_placeholder = original['use_placeholder']
            scene.render.image_settings.file_format = original['image_settings']['file_format']
            scene.render.image_settings.color_mode = original['image_settings']['color_mode']
            context.preferences.view.render_display_type = original['display_mode']
            
            # Restore render engine
            if 'render_engine' in original:
                scene.render.engine = original['render_engine']
                
            # Restore world if it exists
            if 'world' in original and original['world']:
                if original['world'] in bpy.data.worlds:
                    scene.world = bpy.data.worlds[original['world']]
                else:
                    # If the exact world isn't found, create a default world
                    scene.world = bpy.data.worlds.new("Default")
            elif 'world' in original and not original['world']:
                # Original had no world
                scene.world = None
            
            # Restore camera if it exists
            if original['camera'] and original['camera'] in scene.objects:
                scene.camera = scene.objects[original['camera']]
            
            # Restore frame range
            scene.frame_start = original['frame_start']
            scene.frame_end = original['frame_end']
            
            # Restore metadata settings
            scene.render.use_stamp = original['use_stamp']
            scene.render.use_stamp_date = original['use_stamp_date']
            scene.render.use_stamp_time = original['use_stamp_time']
            scene.render.use_stamp_frame = original['use_stamp_frame']
            scene.render.use_stamp_camera = original['use_stamp_camera']
            scene.render.use_stamp_lens = original['use_stamp_lens']
            scene.render.use_stamp_scene = original['use_stamp_scene']
            scene.render.use_stamp_note = original['use_stamp_note']
            scene.render.stamp_note_text = original['stamp_note_text']
            
            # Restore any lights that were disabled
            if hasattr(props, 'original_settings_extended') and props.original_settings_extended:
                try:
                    # Convert the string back to a dictionary
                    light_states = ast.literal_eval(props.original_settings_extended)
                    
                    # Restore each light's settings
                    for light_name, states in light_states.items():
                        if light_name in scene.objects:
                            light = scene.objects[light_name]
                            
                            # Restore visibility states
                            light.hide_viewport = states['hide_viewport']
                            light.hide_render = states['hide_render']
                            light.visible_camera = states['visible_camera']
                            light.visible_diffuse = states['visible_diffuse']
                            light.visible_glossy = states['visible_glossy']
                            light.visible_transmission = states['visible_transmission']
                            light.visible_volume_scatter = states['visible_volume_scatter']
                            
                            print(f"Restored light: {light_name}")
                except Exception as e:
                    self.report({'WARNING'}, f"Could not restore light states: {str(e)}")
            
            # Find 3D views and restore
            for a in context.screen.areas:
                if a.type == 'VIEW_3D':
                    # We don't store these per 3D view in the JSON, so just do a general reset
                    space = a.spaces.active
                    # Reset to solid (common default)
                    space.shading.type = 'SOLID'  
                    # Enable overlays (common default)
                    space.overlay.show_overlays = True
                    
                    # For any camera view, we'll reset
                    for region in a.regions:
                        if region.type == 'WINDOW':
                            region_3d = space.region_3d
                            if region_3d and region_3d.view_perspective == 'CAMERA':
                                # User might want perspective or ortho, but this is safer than leaving camera
                                region_3d.view_perspective = 'PERSP'  
                                if hasattr(region_3d, 'use_local_camera'):
                                    region_3d.use_local_camera = False
            
            # Clear the stored original settings
            props.original_settings = ""
            if hasattr(props, 'original_settings_extended'):
                props.original_settings_extended = ""
            
            self.report({'INFO'}, "Original settings restored")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error restoring settings: {str(e)}")
            return {'CANCELLED'}

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
        # Check for addon updates
        addon_updater_ops.check_for_update_background()
        
        layout = self.layout
        scene = context.scene
        props = scene.basedplayblast
        
        # Main buttons - now integrated with output settings
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("bpl.create_playblast", text="PLAYBLAST", icon='RENDER_ANIMATION')
        row.operator("bpl.view_playblast", text="VIEW", icon='PLAY')
        
        # Show update notice if available
        addon_updater_ops.update_notice_box_ui(self, context)
        
        # Show progress if rendering
        if props.is_rendering:
            box = layout.box()
            box.label(text=props.status_message)
            box.prop(props, "render_progress", text="Progress", slider=True)
        
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
        
        # MOVED BUTTONS: Add the settings apply/restore buttons here, after output settings
        layout.separator()
        
        # Settings apply/restore buttons
        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("bpl.apply_blast_settings", text="Apply Blast Render Settings", icon='GREASEPENCIL')
        row.operator("bpl.restore_original_settings", text="Restore Original Settings", icon='LOOP_BACK')
        
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

# Define the addon preferences class
class BPL_AddonPreferences(AddonPreferences):
    bl_idname = __name__
    
    # Updater preferences
    auto_check_update: BoolProperty(  # type: ignore
        name="Auto-check for Updates",
        description="Automatically check for updates when Blender starts",
        default=True
    )
    
    updater_interval_months: IntProperty(  # type: ignore
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    
    updater_interval_days: IntProperty(  # type: ignore
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
    )
    
    updater_interval_hours: IntProperty(  # type: ignore
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    
    updater_interval_minutes: IntProperty(  # type: ignore
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Updater settings
        addon_updater_ops.update_settings_ui(self, context)

# Registration
classes = (
    BPLProperties,
    BPL_OT_create_playblast,
    BPL_OT_view_playblast,
    BPL_OT_view_latest_playblast,
    BPL_OT_sync_output_path,
    BPL_OT_sync_file_name,
    BPL_OT_apply_blast_settings,
    BPL_OT_restore_original_settings,
    BPL_PT_main_panel,
    BPL_AddonPreferences,
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
    
    # Register addon updater code
    addon_updater_ops.register(bl_info)

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
    
    # Unregister addon updater
    addon_updater_ops.unregister()

if __name__ == "__main__":
    register()