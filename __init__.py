import bpy # type: ignore
import os
import subprocess
import sys
import tempfile
import glob  # Add missing import
from bpy.props import (StringProperty, BoolProperty, IntProperty, EnumProperty, PointerProperty, FloatProperty) # type: ignore
from bpy.types import (Panel, Operator, PropertyGroup, AddonPreferences) # type: ignore
import time

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
    ('H264', "H.264", "Standard H.264 codec with good quality and compression (recommended)"),
    ('H265', "H.265", "H.265 codec with better compression than H.264"),
    ('AV1', "AV1", "Modern AV1 codec with excellent compression"),
    ('MPEG4', "MPEG-4", "MPEG-4 codec for broad compatibility"),
    ('FFV1', "FFV1", "Lossless codec for archival purposes"),
    ('NONE', "None", "No video codec")
]

VIDEO_QUALITY_ITEMS = [
    ('LOWEST', "Lowest", "Lowest quality"),
    ('VERYLOW', "Very Low", "Very low quality"),
    ('LOW', "Low", "Low quality"),
    ('MEDIUM', "Medium", "Medium quality"),
    ('HIGH', "High", "High quality"),
    ('PERC_LOSSLESS', "Perceptually Lossless", "Perceptually lossless quality"),
    ('LOSSLESS', "Lossless", "Lossless quality"),
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

# Helper function to convert quality enum to FFmpeg CRF value
def get_ffmpeg_quality(quality_enum):
    quality_map = {
        'LOWEST': 'HIGH',        # Lowest quality = High CRF value
        'VERYLOW': 'HIGH',
        'LOW': 'MEDIUM', 
        'MEDIUM': 'MEDIUM',
        'HIGH': 'LOW',           # High quality = Low CRF value
        'PERC_LOSSLESS': 'PERC_LOSSLESS',
        'LOSSLESS': 'LOSSLESS',
    }
    return quality_map.get(quality_enum, 'MEDIUM')

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
        name="Use Active Camera",
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
    
    enable_depth_of_field: BoolProperty(  # type: ignore
        name="Enable Depth of Field",
        description="Enable camera depth of field effect in playblast",
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
        default="-c:v h264_nvenc -preset fast -crf 0"
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
    _original_render_engine = None
    _original_cycles_viewport = None
    _use_actual_render = False
    _original_cycles_render = None
    
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
                
                # CRITICAL: Final viewport validation and refresh before render
                if self._space and self._region_3d:
                    # Ensure camera view is active
                    if self._region_3d.view_perspective != 'CAMERA':
                        self._region_3d.view_perspective = 'CAMERA'
                        print("Force-set camera view before render")
                    
                    # Final viewport refresh
                    self._area.tag_redraw()
                    context.view_layer.update()
                    
                    # Add a brief delay to ensure viewport is ready
                    import time
                    time.sleep(0.1)
                
                                # Start the render - choose between actual render or OpenGL based on engine
                if getattr(self, '_use_actual_render', False):
                    # Use actual Cycles rendering for RENDERED mode
                    print(f"Starting Cycles animation render with:")
                    print(f"  - Engine: {context.scene.render.engine}")
                    print(f"  - Samples: {getattr(context.scene.cycles, 'samples', 'unknown')}")
                    print(f"  - Scene camera: {context.scene.camera.name if context.scene.camera else 'None'}")
                    print(f"  - Output format: {context.scene.render.image_settings.file_format}")
                    print(f"  - Output path: {context.scene.render.filepath}")
                    
                    # Use simpler render call without context override to avoid errors
                    bpy.ops.render.render('INVOKE_DEFAULT', animation=True)
                else:
                    # Use OpenGL viewport rendering for other engines
                    override = context.copy()
                    override["area"] = self._area
                    override["region"] = [r for r in self._area.regions if r.type == 'WINDOW'][0]
                        
                    print(f"Starting OpenGL render with:")
                    print(f"  - Area: {self._area.type}")
                    print(f"  - Shading: {self._space.shading.type}")
                    print(f"  - View perspective: {self._region_3d.view_perspective}")
                    print(f"  - Scene camera: {context.scene.camera.name if context.scene.camera else 'None'}")
                    
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
                
                # Check if rendering is complete based on frame count or file existence
                if getattr(self, '_use_actual_render', False):
                    # For Cycles frame-based rendering, check if all frames are rendered
                    output_dir = bpy.path.abspath(context.scene.basedplayblast.output_path)
                    frame_output_dir = os.path.join(output_dir, "frames")
                    expected_frames = self._frame_end - self._frame_start + 1
                    
                    if os.path.exists(frame_output_dir):
                        frame_files = glob.glob(os.path.join(frame_output_dir, "*.png"))
                        frames_rendered = len(frame_files)
                        render_complete = frames_rendered >= expected_frames
                    else:
                        render_complete = False
                else:
                    # For OpenGL rendering, check if output file exists
                    file_ext = get_file_extension(context.scene.basedplayblast.video_format)
                    output_path = bpy.path.abspath(context.scene.render.filepath)
                    full_path = output_path + file_ext
                    render_complete = os.path.exists(full_path)
                
                # When playhead loops back to first frame after rendering all frames
                # or if the rendering is complete, consider it done
                if (current_frame == self._frame_start and self._last_reported_frame >= self._frame_end) or render_complete:
                    # If we've seen the last frame or the rendering is complete, consider it done
                    print(f"Detected playblast completion - Render complete: {render_complete}")
                    
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
        
        # DEBUG: Check engine at very start
        print(f"DEBUG: Engine at very start of invoke: {scene.render.engine}")
        
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
        
        # Store basic original settings for this operator's cleanup
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
        
        # CRITICAL: Store comprehensive original settings NOW, before ANY changes in try block
        if not props.original_settings:
            import json
            
            def safe_getattr(obj, attr, default=None):
                try:
                    return getattr(obj, attr, default)
                except:
                    return default
            
            def make_json_serializable(obj):
                if isinstance(obj, dict):
                    return {key: make_json_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_json_serializable(item) for item in obj]
                elif isinstance(obj, (str, int, float, bool, type(None))):
                    return obj
                else:
                    try:
                        json.dumps(obj)
                        return obj
                    except:
                        return str(obj)
            
            # Store ALL original settings comprehensively - EXACT copy from apply_blast_settings
            original_settings = {
                # SCENE.RENDER - Complete render settings
                'render_engine': scene.render.engine,
                'filepath': scene.render.filepath,
                'resolution_x': scene.render.resolution_x,
                'resolution_y': scene.render.resolution_y,
                'resolution_percentage': scene.render.resolution_percentage,
                'pixel_aspect_x': scene.render.pixel_aspect_x,
                'pixel_aspect_y': scene.render.pixel_aspect_y,
                'use_file_extension': scene.render.use_file_extension,
                'use_overwrite': scene.render.use_overwrite,
                'use_placeholder': scene.render.use_placeholder,
                'frame_start': scene.frame_start,
                'frame_end': scene.frame_end,
                'frame_step': scene.frame_step,
                'frame_current': scene.frame_current,
                
                # Film settings
                'film_transparent': scene.render.film_transparent,
                'filter_size': scene.render.filter_size,
                
                # Performance settings
                'use_persistent_data': scene.render.use_persistent_data,
                'use_simplify': scene.render.use_simplify,
                'simplify_subdivision': scene.render.simplify_subdivision,
                'simplify_child_particles': scene.render.simplify_child_particles,
                'simplify_volumes': scene.render.simplify_volumes,
                'simplify_subdivision_render': safe_getattr(scene.render, 'simplify_subdivision_render', 6),
                'simplify_child_particles_render': safe_getattr(scene.render, 'simplify_child_particles_render', 1.0),
                'simplify_volumes_render': safe_getattr(scene.render, 'simplify_volumes_render', 1.0),
                
                # Motion blur
                'use_motion_blur': scene.render.use_motion_blur,
                'motion_blur_shutter': scene.render.motion_blur_shutter,
                'motion_blur_shutter_curve': str(safe_getattr(scene.render, 'motion_blur_shutter_curve', 'AUTO')),
                'rolling_shutter_type': safe_getattr(scene.render, 'rolling_shutter_type', 'NONE'),
                'rolling_shutter_duration': safe_getattr(scene.render, 'rolling_shutter_duration', 0.1),
                
                # Threading
                'threads_mode': scene.render.threads_mode,
                'threads': scene.render.threads,
                
                # Memory and caching
                'tile_x': safe_getattr(scene.render, 'tile_x', 64),
                'tile_y': safe_getattr(scene.render, 'tile_y', 64),
                'use_save_buffers': safe_getattr(scene.render, 'use_save_buffers', False),
                
                # Preview and display
                'display_mode': context.preferences.view.render_display_type,
                'preview_pixel_size': safe_getattr(scene.render, 'preview_pixel_size', 'AUTO'),
                
                # SCENE.RENDER.IMAGE_SETTINGS - Complete image settings
                'image_settings': {
                    'file_format': scene.render.image_settings.file_format,
                    'color_mode': scene.render.image_settings.color_mode,
                    'color_depth': scene.render.image_settings.color_depth,
                    'compression': scene.render.image_settings.compression,
                    'quality': scene.render.image_settings.quality,
                    'use_preview': scene.render.image_settings.use_preview,
                    'exr_codec': safe_getattr(scene.render.image_settings, 'exr_codec', 'ZIP'),
                    'use_zbuffer': safe_getattr(scene.render.image_settings, 'use_zbuffer', False),
                    'jpeg2k_codec': safe_getattr(scene.render.image_settings, 'jpeg2k_codec', 'JP2'),
                    'tiff_codec': safe_getattr(scene.render.image_settings, 'tiff_codec', 'DEFLATE'),
                },
                
                # SCENE.RENDER.FFMPEG - Complete FFmpeg settings
                'ffmpeg': {
                    'format': scene.render.ffmpeg.format,
                    'codec': scene.render.ffmpeg.codec,
                    'video_bitrate': scene.render.ffmpeg.video_bitrate,
                    'minrate': scene.render.ffmpeg.minrate,
                    'maxrate': scene.render.ffmpeg.maxrate,
                    'buffersize': scene.render.ffmpeg.buffersize,
                    'muxrate': scene.render.ffmpeg.muxrate,
                    'packetsize': scene.render.ffmpeg.packetsize,
                    'constant_rate_factor': scene.render.ffmpeg.constant_rate_factor,
                    'gopsize': scene.render.ffmpeg.gopsize,
                    'use_max_b_frames': safe_getattr(scene.render.ffmpeg, 'use_max_b_frames', False),
                    'max_b_frames': safe_getattr(scene.render.ffmpeg, 'max_b_frames', 2),
                    'use_autosplit': safe_getattr(scene.render.ffmpeg, 'use_autosplit', False),
                    'autosplit_size': safe_getattr(scene.render.ffmpeg, 'autosplit_size', 2048),
                    'audio_codec': scene.render.ffmpeg.audio_codec,
                    'audio_bitrate': scene.render.ffmpeg.audio_bitrate,
                    'audio_channels': scene.render.ffmpeg.audio_channels,
                    'audio_mixrate': scene.render.ffmpeg.audio_mixrate,
                    'audio_volume': scene.render.ffmpeg.audio_volume,
                },
                
                # Scene/world settings
                'world': scene.world.name if scene.world else "",
                'use_nodes': scene.use_nodes,
                
                # Compositing settings
                'use_compositing': scene.render.use_compositing,
                'use_sequencer': scene.render.use_sequencer,
                
                # Border and crop settings
                'use_border': scene.render.use_border,
                'border_min_x': scene.render.border_min_x,
                'border_max_x': scene.render.border_max_x,
                'border_min_y': scene.render.border_min_y,
                'border_max_y': scene.render.border_max_y,
                'use_crop_to_border': scene.render.use_crop_to_border,
                
                # Metadata settings - comprehensive
                'use_stamp': scene.render.use_stamp,
                'use_stamp_date': scene.render.use_stamp_date,
                'use_stamp_time': scene.render.use_stamp_time,
                'use_stamp_frame': scene.render.use_stamp_frame,
                'use_stamp_camera': scene.render.use_stamp_camera,
                'use_stamp_lens': scene.render.use_stamp_lens,
                'use_stamp_scene': scene.render.use_stamp_scene,
                'use_stamp_note': scene.render.use_stamp_note,
                'stamp_note_text': scene.render.stamp_note_text,
                'use_stamp_marker': scene.render.use_stamp_marker,
                'use_stamp_filename': scene.render.use_stamp_filename,
                'use_stamp_render_time': scene.render.use_stamp_render_time,
                'use_stamp_memory': scene.render.use_stamp_memory,
                'use_stamp_hostname': scene.render.use_stamp_hostname,
                'stamp_font_size': scene.render.stamp_font_size,
                'stamp_foreground': [float(x) for x in scene.render.stamp_foreground] if hasattr(scene.render.stamp_foreground, '__iter__') else [1.0, 1.0, 1.0, 1.0],
                'stamp_background': [float(x) for x in scene.render.stamp_background] if hasattr(scene.render.stamp_background, '__iter__') else [0.0, 0.0, 0.0, 0.8],
                
                # Hair settings
                'hair_type': safe_getattr(scene.render, 'hair_type', 'PATH'),
                'hair_subdiv': safe_getattr(scene.render, 'hair_subdiv', 3),
                
                # SCENE.CYCLES - Complete Cycles settings
                'cycles': {
                    'device': safe_getattr(scene.cycles, 'device', 'CPU'),
                    'feature_set': safe_getattr(scene.cycles, 'feature_set', 'SUPPORTED'),
                    'shading_system': safe_getattr(scene.cycles, 'shading_system', 'SVM'),
                    'samples': safe_getattr(scene.cycles, 'samples', 128),
                    'preview_samples': safe_getattr(scene.cycles, 'preview_samples', 32),
                    'aa_samples': safe_getattr(scene.cycles, 'aa_samples', 4),
                    'preview_aa_samples': safe_getattr(scene.cycles, 'preview_aa_samples', 4),
                    'use_denoising': safe_getattr(scene.cycles, 'use_denoising', True),
                    'denoiser': safe_getattr(scene.cycles, 'denoiser', 'OPENIMAGEDENOISE'),
                    'denoising_input_passes': safe_getattr(scene.cycles, 'denoising_input_passes', 'RGB_ALBEDO_NORMAL'),
                    'use_denoising_input_passes': safe_getattr(scene.cycles, 'use_denoising_input_passes', True),
                    'denoising_prefilter': safe_getattr(scene.cycles, 'denoising_prefilter', 'ACCURATE'),
                    'use_adaptive_sampling': safe_getattr(scene.cycles, 'use_adaptive_sampling', True),
                    'adaptive_threshold': safe_getattr(scene.cycles, 'adaptive_threshold', 0.01),
                    'adaptive_min_samples': safe_getattr(scene.cycles, 'adaptive_min_samples', 0),
                    'time_limit': safe_getattr(scene.cycles, 'time_limit', 0.0),
                    'use_preview_adaptive_sampling': safe_getattr(scene.cycles, 'use_preview_adaptive_sampling', False),
                    'preview_adaptive_threshold': safe_getattr(scene.cycles, 'preview_adaptive_threshold', 0.1),
                    'preview_adaptive_min_samples': safe_getattr(scene.cycles, 'preview_adaptive_min_samples', 0),
                    'seed': safe_getattr(scene.cycles, 'seed', 0),
                    'use_animated_seed': safe_getattr(scene.cycles, 'use_animated_seed', False),
                    'sample_clamp_direct': safe_getattr(scene.cycles, 'sample_clamp_direct', 0.0),
                    'sample_clamp_indirect': safe_getattr(scene.cycles, 'sample_clamp_indirect', 0.0),
                    'light_sampling_threshold': safe_getattr(scene.cycles, 'light_sampling_threshold', 0.01),
                    'sample_all_lights_direct': safe_getattr(scene.cycles, 'sample_all_lights_direct', True),
                    'sample_all_lights_indirect': safe_getattr(scene.cycles, 'sample_all_lights_indirect', True),
                    'max_bounces': safe_getattr(scene.cycles, 'max_bounces', 12),
                    'diffuse_bounces': safe_getattr(scene.cycles, 'diffuse_bounces', 4),
                    'glossy_bounces': safe_getattr(scene.cycles, 'glossy_bounces', 4),
                    'transmission_bounces': safe_getattr(scene.cycles, 'transmission_bounces', 12),
                    'volume_bounces': safe_getattr(scene.cycles, 'volume_bounces', 0),
                    'transparent_max_bounces': safe_getattr(scene.cycles, 'transparent_max_bounces', 8),
                    'caustics_reflective': safe_getattr(scene.cycles, 'caustics_reflective', True),
                    'caustics_refractive': safe_getattr(scene.cycles, 'caustics_refractive', True),
                    'filter_type': safe_getattr(scene.cycles, 'filter_type', 'GAUSSIAN'),
                    'filter_width': safe_getattr(scene.cycles, 'filter_width', 1.5),
                    'pixel_filter_width': safe_getattr(scene.cycles, 'pixel_filter_width', 1.5),
                    'use_persistent_data': safe_getattr(scene.cycles, 'use_persistent_data', False),
                    'debug_use_spatial_splits': safe_getattr(scene.cycles, 'debug_use_spatial_splits', False),
                    'debug_use_hair_bvh': safe_getattr(scene.cycles, 'debug_use_hair_bvh', True),
                    'debug_bvh_type': safe_getattr(scene.cycles, 'debug_bvh_type', 'DYNAMIC_BVH'),
                    'debug_use_compact_bvh': safe_getattr(scene.cycles, 'debug_use_compact_bvh', True),
                    'tile_size': safe_getattr(scene.cycles, 'tile_size', 256),
                    'use_auto_tile': safe_getattr(scene.cycles, 'use_auto_tile', False),
                    'progressive': safe_getattr(scene.cycles, 'progressive', 'PATH'),
                    'use_square_samples': safe_getattr(scene.cycles, 'use_square_samples', False),
                    'blur_glossy': safe_getattr(scene.cycles, 'blur_glossy', 0.0),
                    'use_transparent_shadows': safe_getattr(scene.cycles, 'use_transparent_shadows', True),
                    'volume_step_rate': safe_getattr(scene.cycles, 'volume_step_rate', 1.0),
                    'volume_preview_step_rate': safe_getattr(scene.cycles, 'volume_preview_step_rate', 1.0),
                    'volume_max_steps': safe_getattr(scene.cycles, 'volume_max_steps', 1024),
                },
            }
            
            try:
                safe_settings = make_json_serializable(original_settings)
                props.original_settings = json.dumps(safe_settings)
                print(f"Stored comprehensive Cycles settings: samples={original_settings['cycles']['samples']}, engine={original_settings['render_engine']}")
                print(f"DEBUG: JSON engine name stored: {safe_settings['render_engine']}")
                print(f"DEBUG: Current scene engine: {scene.render.engine}")
            except Exception as e:
                print(f"Error storing settings: {e}")
                props.original_settings = ""
        
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
            
            # Set file format first
            scene.render.image_settings.file_format = 'FFMPEG'
            scene.render.ffmpeg.format = props.video_format
            scene.render.ffmpeg.codec = props.video_codec
            scene.render.ffmpeg.constant_rate_factor = get_ffmpeg_quality(props.video_quality)
            
            # Audio settings
            if props.include_audio:
                scene.render.ffmpeg.audio_codec = props.audio_codec
                scene.render.ffmpeg.audio_bitrate = props.audio_bitrate
            else:
                scene.render.ffmpeg.audio_codec = 'NONE'
            
            # Set output path - critical for FFMPEG video output
            file_name = props.file_name
            if '.' in file_name:
                file_name = os.path.splitext(file_name)[0]
            
            # Add frame range to filename
            file_name = file_name.rstrip('_')
            frame_range_str = f"_{self._frame_start}-{self._frame_end}"
            file_name += frame_range_str
            
            # For FFMPEG video, set path with proper video extension and NO frame numbers
            video_ext = get_file_extension(props.video_format)
            scene.render.filepath = os.path.join(output_dir, file_name + video_ext)
            
            # CRITICAL: Disable frame number suffixes for FFMPEG video output
            scene.render.use_file_extension = True
            scene.render.use_overwrite = True
            scene.render.use_placeholder = False
            
            # Confirm FFMPEG format for debugging
            print(f"File format set to: {scene.render.image_settings.file_format}")
            print(f"FFMPEG format: {scene.render.ffmpeg.format}, codec: {scene.render.ffmpeg.codec}")
            print(f"Video output path: {scene.render.filepath}")
            print(f"File extension enabled: {scene.render.use_file_extension}")
            print(f"Overwrite enabled: {scene.render.use_overwrite}")
            print(f"Placeholder disabled: {scene.render.use_placeholder}")
            
            # Set camera if specified
            if not props.use_active_camera and props.camera_object != "NONE":
                camera_obj = context.scene.objects.get(props.camera_object)
                if camera_obj and camera_obj.type == 'CAMERA':
                    scene.camera = camera_obj
                    print(f"Using selected camera: {camera_obj.name}")
                else:
                    self.report({'ERROR'}, f"Selected camera '{props.camera_object}' not found or not a camera")
                    self.cleanup(context)
                    return {'CANCELLED'}
            else:
                # Validate scene camera exists
                if not scene.camera:
                    self.report({'ERROR'}, "No active camera in scene. Please add a camera or select one in the properties.")
                    self.cleanup(context)
                    return {'CANCELLED'}
                print(f"Using scene camera: {scene.camera.name}")
            
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
            
            # Set viewport display mode
            if self._space:
                # CRITICAL: Ensure we have a valid camera first
                if not scene.camera:
                    self.report({'ERROR'}, "No active camera found. Please set an active camera for the scene.")
                    self.cleanup(context)
                    return {'CANCELLED'}
                
                # Set shading type according to display_mode
                if self._space.shading.type != props.display_mode:
                    self._space.shading.type = props.display_mode
                    print(f"Set viewport shading to: {props.display_mode}")
                    
                # Set overlay visibility
                if props.auto_disable_overlays:
                    self._space.overlay.show_overlays = False
                
                # Switch to camera view if needed
                if self._region_3d:
                    self._region_3d.view_perspective = 'CAMERA'
                    if hasattr(self._region_3d, 'use_local_camera'):
                        self._region_3d.use_local_camera = False
                    print(f"Set viewport to camera view")
                
                # CRITICAL: Force viewport refresh and update
                self._area.tag_redraw()
                context.view_layer.update()
                
                # Additional viewport settings based on display mode
                if props.display_mode == 'SOLID':
                    # Ensure proper solid shading settings
                    self._space.shading.color_type = 'MATERIAL'
                    self._space.shading.light = 'STUDIO'
                elif props.display_mode == 'MATERIAL':
                    # Ensure material preview settings
                    self._space.shading.color_type = 'MATERIAL'
                    self._space.shading.light = 'STUDIO'
                elif props.display_mode == 'RENDERED':
                    # CRITICAL: For Cycles, use actual rendering instead of viewport rendering
                    current_engine = scene.render.engine
                    if current_engine == 'CYCLES':
                        print(f"WARNING: Cycles RENDERED mode detected - switching to actual render mode for stability")
                        
                        # Mark that we're using actual rendering instead of viewport rendering
                        self._use_actual_render = True
                        self._original_render_engine = None  # Don't change engine
                        self._original_cycles_viewport = None
                        
                        # CRITICAL: For Cycles, render individual frames and convert to video afterwards
                        # This avoids FFMPEG issues with Cycles animation rendering
                        scene.render.image_settings.file_format = 'PNG'
                        scene.render.image_settings.color_mode = 'RGBA'
                        scene.render.image_settings.compression = 15  # Minimal compression for speed
                        
                        # Set frame-based output path for individual frames
                        frame_output_dir = os.path.join(output_dir, "frames")
                        os.makedirs(frame_output_dir, exist_ok=True)
                        scene.render.filepath = os.path.join(frame_output_dir, file_name + "_")
                        
                        print(f"WARNING: Using frame-based rendering for Cycles stability")
                        print(f"Frame output: {scene.render.filepath}")
                        print(f"Will convert to video after rendering completes")
                        
                        # Apply ultra-fast Cycles settings for playblast
                        cycles = scene.cycles
                        
                        # Store original render settings to restore later
                        if not hasattr(self, '_original_cycles_render'):
                            self._original_cycles_render = {
                                'samples': getattr(cycles, 'samples', 128),
                                'use_denoising': getattr(cycles, 'use_denoising', True),
                                'max_bounces': getattr(cycles, 'max_bounces', 12),
                                'diffuse_bounces': getattr(cycles, 'diffuse_bounces', 4),
                                'glossy_bounces': getattr(cycles, 'glossy_bounces', 4),
                                'transmission_bounces': getattr(cycles, 'transmission_bounces', 12),
                                'volume_bounces': getattr(cycles, 'volume_bounces', 0),
                                'use_adaptive_sampling': getattr(cycles, 'use_adaptive_sampling', True),
                                'adaptive_threshold': getattr(cycles, 'adaptive_threshold', 0.01),
                            }
                        
                        # Apply ultra-fast settings for playblast
                        if hasattr(cycles, 'samples'):
                            cycles.samples = 8  # Very low for speed
                        if hasattr(cycles, 'use_denoising'):
                            cycles.use_denoising = False  # Disable for speed
                        if hasattr(cycles, 'max_bounces'):
                            cycles.max_bounces = 2  # Minimal bounces
                        if hasattr(cycles, 'diffuse_bounces'):
                            cycles.diffuse_bounces = 1
                        if hasattr(cycles, 'glossy_bounces'):
                            cycles.glossy_bounces = 1
                        if hasattr(cycles, 'transmission_bounces'):
                            cycles.transmission_bounces = 1
                        if hasattr(cycles, 'volume_bounces'):
                            cycles.volume_bounces = 0
                        if hasattr(cycles, 'use_adaptive_sampling'):
                            cycles.use_adaptive_sampling = True
                        if hasattr(cycles, 'adaptive_threshold'):
                            cycles.adaptive_threshold = 0.5  # High threshold for fast convergence
                        
                        print(f"Applied ultra-fast Cycles settings: {cycles.samples} samples, no denoising, {cycles.max_bounces} max bounces")
                    else:
                        # For non-Cycles engines, use viewport rendering as normal
                        self._use_actual_render = False
                        self._original_render_engine = None
                        self._original_cycles_viewport = None
                
                print(f"Viewport setup complete for {props.display_mode} mode")
            
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
        
        # Check if we need to convert frames to video for Cycles
        if getattr(self, '_use_actual_render', False):
            self.convert_frames_to_video(context)
        
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
    
    def convert_frames_to_video(self, context):
        """Convert individual PNG frames to video using FFmpeg"""
        scene = context.scene
        props = scene.basedplayblast
        
        try:
            output_dir = bpy.path.abspath(props.output_path)
            frame_output_dir = os.path.join(output_dir, "frames")
            
            # Get file name without extension
            file_name = props.file_name
            if '.' in file_name:
                file_name = os.path.splitext(file_name)[0]
            
            # Add frame range to filename to match the rendered frames
            file_name = file_name.rstrip('_')
            frame_range_str = f"_{self._frame_start}-{self._frame_end}"
            file_name += frame_range_str
            
            # Define video output path
            video_ext = get_file_extension(props.video_format)
            video_output = os.path.join(output_dir, file_name + video_ext)
            
            # Frame pattern for FFmpeg
            frame_pattern = os.path.join(frame_output_dir, file_name + "_%04d.png")
            
            # Build FFmpeg command
            framerate = scene.render.fps / scene.render.fps_base
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",  # Overwrite output file
                "-framerate", str(framerate),
                "-i", frame_pattern,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", "18",  # High quality
                video_output
            ]
            
            print(f"Converting frames to video...")
            print(f"Command: {' '.join(ffmpeg_cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Video conversion successful: {video_output}")
                
                # Clean up frame files
                import glob
                frame_files = glob.glob(os.path.join(frame_output_dir, "*.png"))
                for frame_file in frame_files:
                    try:
                        os.remove(frame_file)
                    except:
                        pass
                
                # Remove frame directory if empty
                try:
                    os.rmdir(frame_output_dir)
                except:
                    pass
                    
            else:
                print(f"FFmpeg error: {result.stderr}")
                self.report({'ERROR'}, f"Video conversion failed: {result.stderr}")
                
        except Exception as e:
            print(f"Error converting frames to video: {str(e)}")
            self.report({'ERROR'}, f"Video conversion error: {str(e)}")
    
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
        
        # PRIMARY RESTORATION: Use self._original_settings first (most reliable)
        if self._original_settings:
            scene = context.scene
            print("Restoring render settings from self._original_settings...")
            
            # Restore render settings - CRITICAL: These must be restored to original values
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
            
            # CRITICAL: Restore frame range to original values - THIS FIXES THE MAIN BUG
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
            
            print(f"Restored resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
            print(f"Restored frame range: {scene.frame_start}-{scene.frame_end}")
        
        # Restore original render engine if it was changed
        if self._original_render_engine is not None:
            context.scene.render.engine = self._original_render_engine
            print(f"Restored original render engine: {self._original_render_engine}")
        
        # Restore original Cycles viewport settings if they were changed
        if self._original_cycles_viewport is not None:
            cycles = context.scene.cycles
            for attr, value in self._original_cycles_viewport.items():
                if hasattr(cycles, attr):
                    setattr(cycles, attr, value)
            print(f"Restored original Cycles viewport settings")
        
        # Restore original Cycles render settings if they were changed
        if self._original_cycles_render is not None:
            cycles = context.scene.cycles
            scene = context.scene
            for attr, value in self._original_cycles_render.items():
                if attr == 'file_format':
                    scene.render.image_settings.file_format = value
                elif hasattr(cycles, attr):
                    setattr(cycles, attr, value)
            print(f"Restored original Cycles render settings")
        
        # SECONDARY RESTORATION: Only use JSON backup if primary restoration didn't work
        # This prevents conflicts and ensures we don't overwrite the correct restoration
        if not self._original_settings and props.original_settings:
            try:
                print("Primary restoration not available, using JSON backup...")
                import json
                original = json.loads(props.original_settings)
                scene = context.scene
                
                def safe_restore(obj, attr, value):
                    try:
                        if hasattr(obj, attr):
                            setattr(obj, attr, value)
                            return True
                    except Exception as e:
                        print(f"Could not restore {attr}: {e}")
                        return False
                
                # Restore render engine first
                if 'render_engine' in original:
                    scene.render.engine = original['render_engine']
                    print(f"Restored render engine to: {original['render_engine']}")
                
                # Restore critical render settings from JSON backup
                scene.render.filepath = original.get('filepath', scene.render.filepath)
                scene.render.resolution_x = original.get('resolution_x', scene.render.resolution_x)
                scene.render.resolution_y = original.get('resolution_y', scene.render.resolution_y)
                scene.render.resolution_percentage = original.get('resolution_percentage', scene.render.resolution_percentage)
                safe_restore(scene.render, 'pixel_aspect_x', original.get('pixel_aspect_x', 1.0))
                safe_restore(scene.render, 'pixel_aspect_y', original.get('pixel_aspect_y', 1.0))
                scene.render.use_file_extension = original.get('use_file_extension', scene.render.use_file_extension)
                scene.render.use_overwrite = original.get('use_overwrite', scene.render.use_overwrite)
                scene.render.use_placeholder = original.get('use_placeholder', scene.render.use_placeholder)
                
                # CRITICAL: Restore frame range from JSON backup
                scene.frame_start = original.get('frame_start', scene.frame_start)
                scene.frame_end = original.get('frame_end', scene.frame_end)
                scene.frame_step = original.get('frame_step', scene.frame_step)
                scene.frame_current = original.get('frame_current', 1)
                
                print(f"JSON backup restored resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
                print(f"JSON backup restored frame range: {scene.frame_start}-{scene.frame_end}")
                
                # Film settings
                scene.render.film_transparent = original.get('film_transparent', scene.render.film_transparent)
                scene.render.filter_size = original.get('filter_size', scene.render.filter_size)
                
                # Performance settings
                scene.render.use_persistent_data = original.get('use_persistent_data', scene.render.use_persistent_data)
                scene.render.use_simplify = original.get('use_simplify', scene.render.use_simplify)
                scene.render.simplify_subdivision = original.get('simplify_subdivision', scene.render.simplify_subdivision)
                scene.render.simplify_child_particles = original.get('simplify_child_particles', scene.render.simplify_child_particles)
                scene.render.simplify_volumes = original.get('simplify_volumes', scene.render.simplify_volumes)
                
                # Motion blur
                scene.render.use_motion_blur = original.get('use_motion_blur', scene.render.use_motion_blur)
                scene.render.motion_blur_shutter = original.get('motion_blur_shutter', scene.render.motion_blur_shutter)
                
                # Threading
                scene.render.threads_mode = original.get('threads_mode', scene.render.threads_mode)
                scene.render.threads = original.get('threads', scene.render.threads)
                
                # Preview and display
                context.preferences.view.render_display_type = original.get('display_mode', context.preferences.view.render_display_type)
                
                # SCENE.RENDER.IMAGE_SETTINGS - Restore image settings
                if 'image_settings' in original:
                    img_settings = original['image_settings']
                    scene.render.image_settings.file_format = img_settings.get('file_format', scene.render.image_settings.file_format)
                    scene.render.image_settings.color_mode = img_settings.get('color_mode', scene.render.image_settings.color_mode)
                    scene.render.image_settings.color_depth = img_settings.get('color_depth', scene.render.image_settings.color_depth)
                    scene.render.image_settings.compression = img_settings.get('compression', scene.render.image_settings.compression)
                    scene.render.image_settings.quality = img_settings.get('quality', scene.render.image_settings.quality)
                    scene.render.image_settings.use_preview = img_settings.get('use_preview', scene.render.image_settings.use_preview)
                
                # Scene/world settings
                scene.use_nodes = original.get('use_nodes', scene.use_nodes)
                
                # Compositing settings
                scene.render.use_compositing = original.get('use_compositing', scene.render.use_compositing)
                scene.render.use_sequencer = original.get('use_sequencer', scene.render.use_sequencer)
                
                # Border and crop settings
                scene.render.use_border = original.get('use_border', scene.render.use_border)
                scene.render.border_min_x = original.get('border_min_x', scene.render.border_min_x)
                scene.render.border_max_x = original.get('border_max_x', scene.render.border_max_x)
                scene.render.border_min_y = original.get('border_min_y', scene.render.border_min_y)
                scene.render.border_max_y = original.get('border_max_y', scene.render.border_max_y)
                scene.render.use_crop_to_border = original.get('use_crop_to_border', scene.render.use_crop_to_border)
                
                # Metadata settings - comprehensive
                scene.render.use_stamp = original.get('use_stamp', scene.render.use_stamp)
                scene.render.use_stamp_date = original.get('use_stamp_date', scene.render.use_stamp_date)
                scene.render.use_stamp_time = original.get('use_stamp_time', scene.render.use_stamp_time)
                scene.render.use_stamp_frame = original.get('use_stamp_frame', scene.render.use_stamp_frame)
                scene.render.use_stamp_camera = original.get('use_stamp_camera', scene.render.use_stamp_camera)
                scene.render.use_stamp_lens = original.get('use_stamp_lens', scene.render.use_stamp_lens)
                scene.render.use_stamp_scene = original.get('use_stamp_scene', scene.render.use_stamp_scene)
                scene.render.use_stamp_note = original.get('use_stamp_note', scene.render.use_stamp_note)
                scene.render.stamp_note_text = original.get('stamp_note_text', scene.render.stamp_note_text)
                scene.render.use_stamp_marker = original.get('use_stamp_marker', scene.render.use_stamp_marker)
                scene.render.use_stamp_filename = original.get('use_stamp_filename', scene.render.use_stamp_filename)
                scene.render.use_stamp_render_time = original.get('use_stamp_render_time', scene.render.use_stamp_render_time)
                scene.render.use_stamp_memory = original.get('use_stamp_memory', scene.render.use_stamp_memory)
                scene.render.use_stamp_hostname = original.get('use_stamp_hostname', scene.render.use_stamp_hostname)
                scene.render.stamp_font_size = original.get('stamp_font_size', scene.render.stamp_font_size)
                if 'stamp_foreground' in original:
                    scene.render.stamp_foreground = original['stamp_foreground']
                if 'stamp_background' in original:
                    scene.render.stamp_background = original['stamp_background']
                
                # SCENE.RENDER.FFMPEG - Restore FFmpeg settings
                if 'ffmpeg' in original:
                    ffmpeg = original['ffmpeg']
                    scene.render.ffmpeg.format = ffmpeg.get('format', scene.render.ffmpeg.format)
                    scene.render.ffmpeg.codec = ffmpeg.get('codec', scene.render.ffmpeg.codec)
                    scene.render.ffmpeg.video_bitrate = ffmpeg.get('video_bitrate', scene.render.ffmpeg.video_bitrate)
                    scene.render.ffmpeg.minrate = ffmpeg.get('minrate', scene.render.ffmpeg.minrate)
                    scene.render.ffmpeg.maxrate = ffmpeg.get('maxrate', scene.render.ffmpeg.maxrate)
                    scene.render.ffmpeg.buffersize = ffmpeg.get('buffersize', scene.render.ffmpeg.buffersize)
                    scene.render.ffmpeg.muxrate = ffmpeg.get('muxrate', scene.render.ffmpeg.muxrate)
                    scene.render.ffmpeg.packetsize = ffmpeg.get('packetsize', scene.render.ffmpeg.packetsize)
                    scene.render.ffmpeg.constant_rate_factor = ffmpeg.get('constant_rate_factor', scene.render.ffmpeg.constant_rate_factor)
                    scene.render.ffmpeg.gopsize = ffmpeg.get('gopsize', scene.render.ffmpeg.gopsize)
                    scene.render.ffmpeg.audio_codec = ffmpeg.get('audio_codec', scene.render.ffmpeg.audio_codec)
                    scene.render.ffmpeg.audio_bitrate = ffmpeg.get('audio_bitrate', scene.render.ffmpeg.audio_bitrate)
                    scene.render.ffmpeg.audio_channels = ffmpeg.get('audio_channels', scene.render.ffmpeg.audio_channels)
                    scene.render.ffmpeg.audio_mixrate = ffmpeg.get('audio_mixrate', scene.render.ffmpeg.audio_mixrate)
                    scene.render.ffmpeg.audio_volume = ffmpeg.get('audio_volume', scene.render.ffmpeg.audio_volume)
                
                # Restore world if it exists
                if 'world' in original and original['world']:
                    if original['world'] in bpy.data.worlds:
                        scene.world = bpy.data.worlds[original['world']]
                elif 'world' in original and not original['world']:
                    scene.world = None
                
                # SCENE.CYCLES - Always restore Cycles settings if available  
                if 'cycles' in original and original['cycles']:
                    cycles_settings = original['cycles']
                    cycles = scene.cycles
                    print(f"Restoring ALL Cycles settings - samples: {cycles_settings.get('samples', 'unknown')}")
                    
                    # Restore ALL Cycles settings comprehensively
                    cycles.device = cycles_settings.get('device', cycles.device)
                    safe_restore(cycles, 'feature_set', cycles_settings.get('feature_set', 'SUPPORTED'))
                    safe_restore(cycles, 'shading_system', cycles_settings.get('shading_system', 'SVM'))
                    cycles.samples = cycles_settings.get('samples', cycles.samples)
                    cycles.preview_samples = cycles_settings.get('preview_samples', cycles.preview_samples)
                    safe_restore(cycles, 'aa_samples', cycles_settings.get('aa_samples', 4))
                    safe_restore(cycles, 'preview_aa_samples', cycles_settings.get('preview_aa_samples', 4))
                    cycles.use_denoising = cycles_settings.get('use_denoising', cycles.use_denoising)
                    safe_restore(cycles, 'denoiser', cycles_settings.get('denoiser', 'OPENIMAGEDENOISE'))
                    safe_restore(cycles, 'denoising_input_passes', cycles_settings.get('denoising_input_passes', 'RGB_ALBEDO_NORMAL'))
                    safe_restore(cycles, 'use_denoising_input_passes', cycles_settings.get('use_denoising_input_passes', True))
                    safe_restore(cycles, 'denoising_prefilter', cycles_settings.get('denoising_prefilter', 'ACCURATE'))
                    cycles.use_adaptive_sampling = cycles_settings.get('use_adaptive_sampling', cycles.use_adaptive_sampling)
                    cycles.adaptive_threshold = cycles_settings.get('adaptive_threshold', cycles.adaptive_threshold)
                    cycles.adaptive_min_samples = cycles_settings.get('adaptive_min_samples', cycles.adaptive_min_samples)
                    safe_restore(cycles, 'time_limit', cycles_settings.get('time_limit', 0.0))
                    safe_restore(cycles, 'use_preview_adaptive_sampling', cycles_settings.get('use_preview_adaptive_sampling', False))
                    safe_restore(cycles, 'preview_adaptive_threshold', cycles_settings.get('preview_adaptive_threshold', 0.1))
                    safe_restore(cycles, 'preview_adaptive_min_samples', cycles_settings.get('preview_adaptive_min_samples', 0))
                    safe_restore(cycles, 'seed', cycles_settings.get('seed', 0))
                    safe_restore(cycles, 'use_animated_seed', cycles_settings.get('use_animated_seed', False))
                    safe_restore(cycles, 'sample_clamp_direct', cycles_settings.get('sample_clamp_direct', 0.0))
                    safe_restore(cycles, 'sample_clamp_indirect', cycles_settings.get('sample_clamp_indirect', 0.0))
                    cycles.light_sampling_threshold = cycles_settings.get('light_sampling_threshold', cycles.light_sampling_threshold)
                    safe_restore(cycles, 'sample_all_lights_direct', cycles_settings.get('sample_all_lights_direct', True))
                    safe_restore(cycles, 'sample_all_lights_indirect', cycles_settings.get('sample_all_lights_indirect', True))
                    cycles.max_bounces = cycles_settings.get('max_bounces', cycles.max_bounces)
                    cycles.diffuse_bounces = cycles_settings.get('diffuse_bounces', cycles.diffuse_bounces)
                    cycles.glossy_bounces = cycles_settings.get('glossy_bounces', cycles.glossy_bounces)
                    cycles.transmission_bounces = cycles_settings.get('transmission_bounces', cycles.transmission_bounces)
                    cycles.volume_bounces = cycles_settings.get('volume_bounces', cycles.volume_bounces)
                    safe_restore(cycles, 'transparent_max_bounces', cycles_settings.get('transparent_max_bounces', 8))
                    cycles.caustics_reflective = cycles_settings.get('caustics_reflective', cycles.caustics_reflective)
                    cycles.caustics_refractive = cycles_settings.get('caustics_refractive', cycles.caustics_refractive)
                    safe_restore(cycles, 'filter_type', cycles_settings.get('filter_type', 'GAUSSIAN'))
                    safe_restore(cycles, 'filter_width', cycles_settings.get('filter_width', 1.5))
                    cycles.pixel_filter_width = cycles_settings.get('pixel_filter_width', cycles.pixel_filter_width)
                    cycles.use_persistent_data = cycles_settings.get('use_persistent_data', cycles.use_persistent_data)
                    safe_restore(cycles, 'debug_use_spatial_splits', cycles_settings.get('debug_use_spatial_splits', False))
                    safe_restore(cycles, 'debug_use_hair_bvh', cycles_settings.get('debug_use_hair_bvh', True))
                    safe_restore(cycles, 'debug_bvh_type', cycles_settings.get('debug_bvh_type', 'DYNAMIC_BVH'))
                    safe_restore(cycles, 'debug_use_compact_bvh', cycles_settings.get('debug_use_compact_bvh', True))
                    safe_restore(cycles, 'tile_size', cycles_settings.get('tile_size', 256))
                    safe_restore(cycles, 'use_auto_tile', cycles_settings.get('use_auto_tile', False))
                    safe_restore(cycles, 'progressive', cycles_settings.get('progressive', 'PATH'))
                    safe_restore(cycles, 'use_square_samples', cycles_settings.get('use_square_samples', False))
                    safe_restore(cycles, 'blur_glossy', cycles_settings.get('blur_glossy', 0.0))
                    safe_restore(cycles, 'use_transparent_shadows', cycles_settings.get('use_transparent_shadows', True))
                    safe_restore(cycles, 'volume_step_rate', cycles_settings.get('volume_step_rate', 1.0))
                    safe_restore(cycles, 'volume_preview_step_rate', cycles_settings.get('volume_preview_step_rate', 1.0))
                    safe_restore(cycles, 'volume_max_steps', cycles_settings.get('volume_max_steps', 1024))
                    
                    print(f"ALL Cycles settings restoration completed")
                
                # Clear the stored settings
                props.original_settings = ""
                print("Comprehensive settings restoration completed")
                
            except Exception as e:
                print(f"Error restoring comprehensive settings: {e}")
        
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

# New operator to apply user defaults
class BPL_OT_apply_user_defaults(Operator):
    bl_idname = "bpl.apply_user_defaults"
    bl_label = "Apply User Defaults"
    bl_description = "Apply the user's default settings from Add-on Preferences to the current scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        props = context.scene.basedplayblast

        props.video_quality = prefs.default_video_quality
        props.use_custom_ffmpeg_args = prefs.default_use_custom_ffmpeg_args
        props.custom_ffmpeg_args = prefs.default_ffmpeg_args

        self.report({'INFO'}, "User defaults applied to scene.")
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
        
        # First, save ALL original settings - always save fresh settings each time
        # Clear any previously saved settings to ensure we get current state
        props.original_settings = ""
        props.original_settings_extended = ""
        
        # TEMPORARY TEST: Set a minimal test setting to verify restore works
        import json
        test_settings = {
            'render_engine': scene.render.engine,
            'cycles': {
                'samples': getattr(scene.cycles, 'samples', 128),
                'use_denoising': getattr(scene.cycles, 'use_denoising', True)
            }
        }
        props.original_settings = json.dumps(test_settings)
        print(f"TEMP TEST: Set minimal test settings - engine: {test_settings['render_engine']}, cycles samples: {test_settings['cycles']['samples']}")
        
        import json
        
        # COMPREHENSIVE SETTINGS STORAGE - Save EVERYTHING
        print(f"Saving comprehensive render settings for engine: {scene.render.engine}")
        print(f"DEBUG: Starting comprehensive settings save process")
        
        def safe_getattr(obj, attr, default=None):
            """Safely get attribute with fallback"""
            try:
                return getattr(obj, attr, default)
            except:
                return default
        
        def make_json_serializable(obj):
            """Convert object to JSON-serializable format"""
            if isinstance(obj, dict):
                # Handle dictionaries - recursively process values
                return {key: make_json_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, (list, tuple)):
                # Handle lists and tuples
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                # Already JSON serializable
                return obj
            else:
                # Convert everything else to string
                try:
                    json.dumps(obj)  # Test if it's serializable
                    return obj
                except:
                    return str(obj)
        
        original_settings = {
                # SCENE.RENDER - Complete render settings
                'render_engine': scene.render.engine,
                'filepath': scene.render.filepath,
                'resolution_x': scene.render.resolution_x,
                'resolution_y': scene.render.resolution_y,
                'resolution_percentage': scene.render.resolution_percentage,
                'pixel_aspect_x': scene.render.pixel_aspect_x,
                'pixel_aspect_y': scene.render.pixel_aspect_y,
                'use_file_extension': scene.render.use_file_extension,
                'use_overwrite': scene.render.use_overwrite,
                'use_placeholder': scene.render.use_placeholder,
                'frame_start': scene.frame_start,
                'frame_end': scene.frame_end,
                'frame_step': scene.frame_step,
                'frame_current': scene.frame_current,
                
                # Film settings
                'film_transparent': scene.render.film_transparent,
                'filter_size': scene.render.filter_size,
                
                # Performance settings
                'use_persistent_data': scene.render.use_persistent_data,
                'use_simplify': scene.render.use_simplify,
                'simplify_subdivision': scene.render.simplify_subdivision,
                'simplify_child_particles': scene.render.simplify_child_particles,
                'simplify_volumes': scene.render.simplify_volumes,
                'simplify_subdivision_render': safe_getattr(scene.render, 'simplify_subdivision_render', 6),
                'simplify_child_particles_render': safe_getattr(scene.render, 'simplify_child_particles_render', 1.0),
                'simplify_volumes_render': safe_getattr(scene.render, 'simplify_volumes_render', 1.0),
                
                # Motion blur
                'use_motion_blur': scene.render.use_motion_blur,
                'motion_blur_shutter': scene.render.motion_blur_shutter,
                'motion_blur_shutter_curve': str(safe_getattr(scene.render, 'motion_blur_shutter_curve', 'AUTO')),
                'rolling_shutter_type': safe_getattr(scene.render, 'rolling_shutter_type', 'NONE'),
                'rolling_shutter_duration': safe_getattr(scene.render, 'rolling_shutter_duration', 0.1),
                
                # Threading
                'threads_mode': scene.render.threads_mode,
                'threads': scene.render.threads,
                
                # Memory and caching
                'tile_x': safe_getattr(scene.render, 'tile_x', 64),
                'tile_y': safe_getattr(scene.render, 'tile_y', 64),
                'use_save_buffers': safe_getattr(scene.render, 'use_save_buffers', False),
                
                # Preview and display
                'display_mode': context.preferences.view.render_display_type,
                'preview_pixel_size': safe_getattr(scene.render, 'preview_pixel_size', 'AUTO'),
                
                # SCENE.RENDER.IMAGE_SETTINGS - Complete image settings
                'image_settings': {
                    'file_format': scene.render.image_settings.file_format,
                    'color_mode': scene.render.image_settings.color_mode,
                    'color_depth': scene.render.image_settings.color_depth,
                    'compression': scene.render.image_settings.compression,
                    'quality': scene.render.image_settings.quality,
                    'use_preview': scene.render.image_settings.use_preview,
                    'exr_codec': safe_getattr(scene.render.image_settings, 'exr_codec', 'ZIP'),
                    'use_zbuffer': safe_getattr(scene.render.image_settings, 'use_zbuffer', False),
                    'jpeg2k_codec': safe_getattr(scene.render.image_settings, 'jpeg2k_codec', 'JP2'),
                    'tiff_codec': safe_getattr(scene.render.image_settings, 'tiff_codec', 'DEFLATE'),
                },
                
                # SCENE.RENDER.FFMPEG - Complete FFmpeg settings
                'ffmpeg': {
                    'format': scene.render.ffmpeg.format,
                    'codec': scene.render.ffmpeg.codec,
                    'video_bitrate': scene.render.ffmpeg.video_bitrate,
                    'minrate': scene.render.ffmpeg.minrate,
                    'maxrate': scene.render.ffmpeg.maxrate,
                    'buffersize': scene.render.ffmpeg.buffersize,
                    'muxrate': scene.render.ffmpeg.muxrate,
                    'packetsize': scene.render.ffmpeg.packetsize,
                    'constant_rate_factor': scene.render.ffmpeg.constant_rate_factor,
                    'gopsize': scene.render.ffmpeg.gopsize,
                    'use_max_b_frames': safe_getattr(scene.render.ffmpeg, 'use_max_b_frames', False),
                    'max_b_frames': safe_getattr(scene.render.ffmpeg, 'max_b_frames', 2),
                    'use_autosplit': safe_getattr(scene.render.ffmpeg, 'use_autosplit', False),
                    'autosplit_size': safe_getattr(scene.render.ffmpeg, 'autosplit_size', 2048),
                    'audio_codec': scene.render.ffmpeg.audio_codec,
                    'audio_bitrate': scene.render.ffmpeg.audio_bitrate,
                    'audio_channels': scene.render.ffmpeg.audio_channels,
                    'audio_mixrate': scene.render.ffmpeg.audio_mixrate,
                    'audio_volume': scene.render.ffmpeg.audio_volume,
                },
                
                # Scene/world settings
                'world': scene.world.name if scene.world else "",
                'use_nodes': scene.use_nodes,
                
                # Compositing settings
                'use_compositing': scene.render.use_compositing,
                'use_sequencer': scene.render.use_sequencer,
                
                # Border and crop settings
                'use_border': scene.render.use_border,
                'border_min_x': scene.render.border_min_x,
                'border_max_x': scene.render.border_max_x,
                'border_min_y': scene.render.border_min_y,
                'border_max_y': scene.render.border_max_y,
                'use_crop_to_border': scene.render.use_crop_to_border,
                
                # Metadata settings - comprehensive
                'use_stamp': scene.render.use_stamp,
                'use_stamp_date': scene.render.use_stamp_date,
                'use_stamp_time': scene.render.use_stamp_time,
                'use_stamp_frame': scene.render.use_stamp_frame,
                'use_stamp_camera': scene.render.use_stamp_camera,
                'use_stamp_lens': scene.render.use_stamp_lens,
                'use_stamp_scene': scene.render.use_stamp_scene,
                'use_stamp_note': scene.render.use_stamp_note,
                'stamp_note_text': scene.render.stamp_note_text,
                'use_stamp_marker': scene.render.use_stamp_marker,
                'use_stamp_filename': scene.render.use_stamp_filename,
                'use_stamp_render_time': scene.render.use_stamp_render_time,
                'use_stamp_memory': scene.render.use_stamp_memory,
                'use_stamp_hostname': scene.render.use_stamp_hostname,
                'stamp_font_size': scene.render.stamp_font_size,
                'stamp_foreground': [float(x) for x in scene.render.stamp_foreground] if hasattr(scene.render.stamp_foreground, '__iter__') else [1.0, 1.0, 1.0, 1.0],
                'stamp_background': [float(x) for x in scene.render.stamp_background] if hasattr(scene.render.stamp_background, '__iter__') else [0.0, 0.0, 0.0, 0.8],
                
                # Hair settings
                'hair_type': safe_getattr(scene.render, 'hair_type', 'PATH'),
                'hair_subdiv': safe_getattr(scene.render, 'hair_subdiv', 3),
        }
        
        # SCENE.CYCLES - Always save Cycles settings regardless of current engine
        print(f"DEBUG: About to start Cycles saving section")
        try:
            cycles = scene.cycles
            print(f"Attempting to save Cycles settings...")
            original_settings['cycles'] = {
                    'device': safe_getattr(cycles, 'device', 'CPU'),
                    'feature_set': safe_getattr(cycles, 'feature_set', 'SUPPORTED'),
                    'shading_system': safe_getattr(cycles, 'shading_system', 'SVM'),
                    'samples': safe_getattr(cycles, 'samples', 128),
                    'preview_samples': safe_getattr(cycles, 'preview_samples', 32),
                    'aa_samples': safe_getattr(cycles, 'aa_samples', 4),
                    'preview_aa_samples': safe_getattr(cycles, 'preview_aa_samples', 4),
                    'use_denoising': safe_getattr(cycles, 'use_denoising', True),
                    'denoiser': safe_getattr(cycles, 'denoiser', 'OPENIMAGEDENOISE'),
                    'denoising_input_passes': safe_getattr(cycles, 'denoising_input_passes', 'RGB_ALBEDO_NORMAL'),
                    'use_denoising_input_passes': safe_getattr(cycles, 'use_denoising_input_passes', True),
                    'denoising_prefilter': safe_getattr(cycles, 'denoising_prefilter', 'ACCURATE'),
                    'use_adaptive_sampling': safe_getattr(cycles, 'use_adaptive_sampling', True),
                    'adaptive_threshold': safe_getattr(cycles, 'adaptive_threshold', 0.01),
                    'adaptive_min_samples': safe_getattr(cycles, 'adaptive_min_samples', 0),
                    'time_limit': safe_getattr(cycles, 'time_limit', 0.0),
                    'use_preview_adaptive_sampling': safe_getattr(cycles, 'use_preview_adaptive_sampling', False),
                    'preview_adaptive_threshold': safe_getattr(cycles, 'preview_adaptive_threshold', 0.1),
                    'preview_adaptive_min_samples': safe_getattr(cycles, 'preview_adaptive_min_samples', 0),
                    'seed': safe_getattr(cycles, 'seed', 0),
                    'use_animated_seed': safe_getattr(cycles, 'use_animated_seed', False),
                    'sample_clamp_direct': safe_getattr(cycles, 'sample_clamp_direct', 0.0),
                    'sample_clamp_indirect': safe_getattr(cycles, 'sample_clamp_indirect', 0.0),
                    'light_sampling_threshold': safe_getattr(cycles, 'light_sampling_threshold', 0.01),
                    'sample_all_lights_direct': safe_getattr(cycles, 'sample_all_lights_direct', True),
                    'sample_all_lights_indirect': safe_getattr(cycles, 'sample_all_lights_indirect', True),
                    'max_bounces': safe_getattr(cycles, 'max_bounces', 12),
                    'diffuse_bounces': safe_getattr(cycles, 'diffuse_bounces', 4),
                    'glossy_bounces': safe_getattr(cycles, 'glossy_bounces', 4),
                    'transmission_bounces': safe_getattr(cycles, 'transmission_bounces', 12),
                    'volume_bounces': safe_getattr(cycles, 'volume_bounces', 0),
                    'transparent_max_bounces': safe_getattr(cycles, 'transparent_max_bounces', 8),
                    'caustics_reflective': safe_getattr(cycles, 'caustics_reflective', True),
                    'caustics_refractive': safe_getattr(cycles, 'caustics_refractive', True),
                    'filter_type': safe_getattr(cycles, 'filter_type', 'GAUSSIAN'),
                    'filter_width': safe_getattr(cycles, 'filter_width', 1.5),
                    'pixel_filter_width': safe_getattr(cycles, 'pixel_filter_width', 1.5),
                    'use_persistent_data': safe_getattr(cycles, 'use_persistent_data', False),
                    'debug_use_spatial_splits': safe_getattr(cycles, 'debug_use_spatial_splits', False),
                    'debug_use_hair_bvh': safe_getattr(cycles, 'debug_use_hair_bvh', True),
                    'debug_bvh_type': safe_getattr(cycles, 'debug_bvh_type', 'DYNAMIC_BVH'),
                    'debug_use_compact_bvh': safe_getattr(cycles, 'debug_use_compact_bvh', True),
                    'tile_size': safe_getattr(cycles, 'tile_size', 256),
                    'use_auto_tile': safe_getattr(cycles, 'use_auto_tile', False),
                    'progressive': safe_getattr(cycles, 'progressive', 'PATH'),
                    'use_square_samples': safe_getattr(cycles, 'use_square_samples', False),
                    'blur_glossy': safe_getattr(cycles, 'blur_glossy', 0.0),
                    'use_transparent_shadows': safe_getattr(cycles, 'use_transparent_shadows', True),
                    'volume_step_rate': safe_getattr(cycles, 'volume_step_rate', 1.0),
                    'volume_preview_step_rate': safe_getattr(cycles, 'volume_preview_step_rate', 1.0),
                    'volume_max_steps': safe_getattr(cycles, 'volume_max_steps', 1024),
            }
            print(f"Successfully saved Cycles settings with {len(original_settings['cycles'])} keys")
        except Exception as e:
            print(f"Could not save Cycles settings: {e}")
            original_settings['cycles'] = {}
            print(f"Set empty Cycles settings due to error")
                
        # SCENE.EEVEE - Always save EEVEE settings regardless of current engine
        try:
            eevee_attr = 'eevee' if hasattr(scene, 'eevee') else 'eevee_next'
            eevee = getattr(scene, eevee_attr) if hasattr(scene, eevee_attr) else None
            if eevee:
                original_settings['eevee'] = {
                    'taa_render_samples': safe_getattr(eevee, 'taa_render_samples', 64),
                    'taa_samples': safe_getattr(eevee, 'taa_samples', 16),
                    'use_bloom': safe_getattr(eevee, 'use_bloom', False),
                    'bloom_threshold': safe_getattr(eevee, 'bloom_threshold', 0.8),
                    'bloom_knee': safe_getattr(eevee, 'bloom_knee', 0.5),
                    'bloom_radius': safe_getattr(eevee, 'bloom_radius', 6.5),
                    'bloom_intensity': safe_getattr(eevee, 'bloom_intensity', 0.05),
                    'use_ssr': safe_getattr(eevee, 'use_ssr', False),
                    'use_ssr_refraction': safe_getattr(eevee, 'use_ssr_refraction', False),
                    'ssr_max_roughness': safe_getattr(eevee, 'ssr_max_roughness', 0.5),
                    'ssr_thickness': safe_getattr(eevee, 'ssr_thickness', 0.2),
                    'ssr_border_fade': safe_getattr(eevee, 'ssr_border_fade', 0.075),
                    'ssr_firefly_fac': safe_getattr(eevee, 'ssr_firefly_fac', 10.0),
                    'use_motion_blur': safe_getattr(eevee, 'use_motion_blur', False),
                    'motion_blur_samples': safe_getattr(eevee, 'motion_blur_samples', 8),
                    'motion_blur_shutter': safe_getattr(eevee, 'motion_blur_shutter', 0.5),
                    'use_volumetric_lights': safe_getattr(eevee, 'use_volumetric_lights', False),
                    'volumetric_start': safe_getattr(eevee, 'volumetric_start', 0.1),
                    'volumetric_end': safe_getattr(eevee, 'volumetric_end', 100.0),
                    'volumetric_tile_size': safe_getattr(eevee, 'volumetric_tile_size', '8'),
                    'volumetric_samples': safe_getattr(eevee, 'volumetric_samples', 64),
                    'volumetric_sample_distribution': safe_getattr(eevee, 'volumetric_sample_distribution', 0.8),
                    'use_volumetric_shadows': safe_getattr(eevee, 'use_volumetric_shadows', False),
                    'volumetric_shadow_samples': safe_getattr(eevee, 'volumetric_shadow_samples', 16),
                    'gi_diffuse_bounces': safe_getattr(eevee, 'gi_diffuse_bounces', 3),
                    'gi_cubemap_resolution': safe_getattr(eevee, 'gi_cubemap_resolution', '512'),
                    'gi_visibility_resolution': safe_getattr(eevee, 'gi_visibility_resolution', '16'),
                    'gi_irradiance_smoothing': safe_getattr(eevee, 'gi_irradiance_smoothing', 0.1),
                    'gi_glossy_clamp': safe_getattr(eevee, 'gi_glossy_clamp', 0.0),
                    'gi_filter_quality': safe_getattr(eevee, 'gi_filter_quality', 1.0),
                    'use_persistent_data': safe_getattr(eevee, 'use_persistent_data', False),
                    'shadow_cube_size': safe_getattr(eevee, 'shadow_cube_size', '512'),
                    'shadow_cascade_size': safe_getattr(eevee, 'shadow_cascade_size', '1024'),
                    'use_shadow_high_bitdepth': safe_getattr(eevee, 'use_shadow_high_bitdepth', False),
                    'use_soft_shadows': safe_getattr(eevee, 'use_soft_shadows', True),
                    'use_shadows': safe_getattr(eevee, 'use_shadows', True),
                    'light_threshold': safe_getattr(eevee, 'light_threshold', 0.01),
                    'use_gtao': safe_getattr(eevee, 'use_gtao', False),
                    'gtao_distance': safe_getattr(eevee, 'gtao_distance', 0.2),
                    'gtao_factor': safe_getattr(eevee, 'gtao_factor', 1.0),
                    'gtao_quality': safe_getattr(eevee, 'gtao_quality', 0.25),
                    'use_overscan': safe_getattr(eevee, 'use_overscan', False),
                    'overscan_size': safe_getattr(eevee, 'overscan_size', 3.0),
                    'shadow_ray_count': safe_getattr(eevee, 'shadow_ray_count', 1),
                    'shadow_step_count': safe_getattr(eevee, 'shadow_step_count', 6),
                    'fast_gi_method': safe_getattr(eevee, 'fast_gi_method', 'GLOBAL_ILLUMINATION'),
                    'fast_gi_ray_count': safe_getattr(eevee, 'fast_gi_ray_count', 4),
                    'fast_gi_step_count': safe_getattr(eevee, 'fast_gi_step_count', 4),
                    'fast_gi_quality': safe_getattr(eevee, 'fast_gi_quality', 0.25),
                    'fast_gi_distance': safe_getattr(eevee, 'fast_gi_distance', 10.0),
                }
                print("Saved EEVEE settings")
            else:
                original_settings['eevee'] = {}
        except Exception as e:
            print(f"Could not save EEVEE settings: {e}")
            original_settings['eevee'] = {}
                
        # SCENE.DISPLAY (WORKBENCH) settings
        try:
            original_settings['workbench'] = {
                'shading_type': scene.display.shading.type,
                'light': scene.display.shading.light,
                'color_type': scene.display.shading.color_type,
                'single_color': list(safe_getattr(scene.display.shading, 'single_color', (0.8, 0.8, 0.8))),
                'background_type': safe_getattr(scene.display.shading, 'background_type', 'THEME'),
                'background_color': list(safe_getattr(scene.display.shading, 'background_color', (0.05, 0.05, 0.05))),
                'cavity_ridge_factor': safe_getattr(scene.display.shading, 'cavity_ridge_factor', 1.0),
                'cavity_valley_factor': safe_getattr(scene.display.shading, 'cavity_valley_factor', 1.0),
                'curvature_ridge_factor': safe_getattr(scene.display.shading, 'curvature_ridge_factor', 1.0),
                'curvature_valley_factor': safe_getattr(scene.display.shading, 'curvature_valley_factor', 1.0),
                'render_aa': safe_getattr(scene.display, 'render_aa', 'FXAA'),
                'show_cavity': safe_getattr(scene.display.shading, 'show_cavity', False),
                'show_object_outline': safe_getattr(scene.display.shading, 'show_object_outline', False),
                'show_specular_highlight': safe_getattr(scene.display.shading, 'show_specular_highlight', True),
                'use_dof': safe_getattr(scene.display.shading, 'use_dof', False),
                'show_xray': safe_getattr(scene.display.shading, 'show_xray', False),
                'xray_alpha': safe_getattr(scene.display.shading, 'xray_alpha', 0.5),
                'show_shadows': safe_getattr(scene.display.shading, 'show_shadows', False),
                'shadow_intensity': safe_getattr(scene.display.shading, 'shadow_intensity', 0.5),
                'studio_light': safe_getattr(scene.display.shading, 'studio_light', 'DEFAULT'),
                'studiolight_rotate_z': safe_getattr(scene.display.shading, 'studiolight_rotate_z', 0.0),
                'studiolight_intensity': safe_getattr(scene.display.shading, 'studiolight_intensity', 1.0),
                'studiolight_background_alpha': safe_getattr(scene.display.shading, 'studiolight_background_alpha', 0.0),
                'studiolight_background_blur': safe_getattr(scene.display.shading, 'studiolight_background_blur', 0.0),
            }
            print("Saved Workbench settings")
        except Exception as e:
            print(f"Could not save Workbench settings: {e}")
            original_settings['workbench'] = {}
            
        # Try to save the settings with detailed error reporting
        try:
            # Make sure all objects are JSON serializable
            safe_settings = make_json_serializable(original_settings)
            props.original_settings = json.dumps(safe_settings)
            print(f"Comprehensive settings saved to JSON ({len(props.original_settings)} characters)")
            print(f"Saved settings include: {list(original_settings.keys())}")
            print(f"Cycles settings saved: {'cycles' in original_settings and bool(original_settings['cycles'])}")
            if 'cycles' in original_settings:
                print(f"Cycles settings keys: {list(original_settings['cycles'].keys())}")
            print(f"EEVEE settings saved: {'eevee' in original_settings and bool(original_settings['eevee'])}")
        except Exception as json_error:
            print(f"ERROR: Failed to save settings to JSON: {str(json_error)}")
            import traceback
            traceback.print_exc()
            # Don't clear the test settings - keep them so restore works
            if not props.original_settings:
                print(f"FALLBACK: Using minimal test settings since comprehensive save failed")
            else:
                print(f"KEEPING existing settings since JSON save failed")
        
        try:
            # Apply render engine and settings based on display mode
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
                        
                        # Set minimal ray and step settings for maximum performance
                        if hasattr(eevee, 'gi_irradiance_smoothing'):
                            eevee.gi_irradiance_smoothing = 0.1  # Minimal smoothing
                        if hasattr(eevee, 'gi_glossy_clamp'):
                            eevee.gi_glossy_clamp = 0.0  # No clamping
                        
                        # Set raytracing settings to minimum (1 ray, 2 steps)
                        if hasattr(eevee, 'ssr_max_roughness'):
                            eevee.ssr_max_roughness = 0.5  # Limit SSR roughness
                        if hasattr(eevee, 'ssr_thickness'):
                            eevee.ssr_thickness = 0.2  # Thin SSR thickness
                        if hasattr(eevee, 'ssr_border_fade'):
                            eevee.ssr_border_fade = 0.075  # Minimal border fade
                        if hasattr(eevee, 'ssr_firefly_fac'):
                            eevee.ssr_firefly_fac = 10.0  # Standard firefly suppression
                            
                        # Set shadow raytracing to minimal (1 ray, 2 steps)
                        if hasattr(eevee, 'shadow_ray_count'):
                            eevee.shadow_ray_count = 1  # 1 ray for shadows
                        if hasattr(eevee, 'shadow_step_count'):
                            eevee.shadow_step_count = 2  # 2 steps for shadows
                            
                        # Set fast GI to minimal settings (1 ray, 2 steps)
                        if hasattr(eevee, 'fast_gi_method'):
                            eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'  # Use valid method
                        if hasattr(eevee, 'fast_gi_ray_count'):
                            eevee.fast_gi_ray_count = 1  # 1 ray for fast GI
                        if hasattr(eevee, 'fast_gi_step_count'):
                            eevee.fast_gi_step_count = 2  # 2 steps for fast GI
                        if hasattr(eevee, 'fast_gi_quality'):
                            eevee.fast_gi_quality = 0.25  # Low quality for speed
                        if hasattr(eevee, 'fast_gi_distance'):
                            eevee.fast_gi_distance = 1.0  # Short distance
                                
                            # Enable persistent data if available for faster animation rendering
                            if hasattr(eevee, 'use_persistent_data'):
                                eevee.use_persistent_data = True
                                print(f"Enabled persistent data for faster EEVEE animation rendering")
                                
                        print(f"Set EEVEE raytracing to 1 ray, 2 steps for maximum performance")
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
                            cycles.adaptive_threshold = 0.8  # Even higher threshold = faster convergence
                        if hasattr(cycles, 'adaptive_min_samples'):
                            cycles.adaptive_min_samples = 0  # Allow adaptive sampling to stop early
                            
                        # Use fastest integrator settings
                        if hasattr(cycles, 'light_sampling_threshold'):
                            cycles.light_sampling_threshold = 1.0  # Maximum threshold for fastest convergence
                            
                        # Disable expensive sampling features
                        if hasattr(cycles, 'sample_clamp_direct'):
                            cycles.sample_clamp_direct = 0.0  # No clamping for speed
                        if hasattr(cycles, 'sample_clamp_indirect'):
                            cycles.sample_clamp_indirect = 0.0  # No clamping for speed
                        if hasattr(cycles, 'blur_glossy'):
                            cycles.blur_glossy = 0.0  # Disable glossy blur
                        if hasattr(cycles, 'sample_all_lights_direct'):
                            cycles.sample_all_lights_direct = False  # Don't sample all lights
                        if hasattr(cycles, 'sample_all_lights_indirect'):
                            cycles.sample_all_lights_indirect = False  # Don't sample all lights
                            
                        # Use fastest filter and preview settings
                        if hasattr(cycles, 'filter_type'):
                            cycles.filter_type = 'BOX'  # Fastest filter type
                        if hasattr(cycles, 'preview_samples'):
                            cycles.preview_samples = 1  # Minimum viewport samples
                        if hasattr(cycles, 'aa_samples'):
                            cycles.aa_samples = 1  # Minimum anti-aliasing samples
                            
                        # Disable expensive transparency features
                        if hasattr(cycles, 'use_transparent_shadows'):
                            cycles.use_transparent_shadows = False
                        if hasattr(cycles, 'transparent_max_bounces'):
                            cycles.transparent_max_bounces = 0  # No transparent bounces
                            
                        # Optimize tile size for faster rendering
                        if hasattr(cycles, 'tile_size'):
                            cycles.tile_size = 64  # Small tiles for faster feedback
                        if hasattr(cycles, 'use_auto_tile'):
                            cycles.use_auto_tile = True  # Let Cycles optimize tile size
                            
                        # Use fastest integrator path
                        if hasattr(cycles, 'progressive'):
                            cycles.progressive = 'PATH'  # Use path tracing (usually fastest)
                            
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
                                
                        # Additional GPU optimizations
                        if hasattr(cycles, 'feature_set'):
                            cycles.feature_set = 'SUPPORTED'  # Use only supported GPU features
                        if hasattr(cycles, 'use_cpu_device'):
                            cycles.use_cpu_device = False  # Force GPU only if available
                                
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
                    # Completely remove scene world - critical for studio lights
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
                            
                        # CRITICAL: Always disable shadows and raytracing for material preview
                        if hasattr(eevee, 'use_shadows'):
                            eevee.use_shadows = False
                            print(f"Disabled shadows for material preview")
                        if hasattr(eevee, 'use_soft_shadows'):
                            eevee.use_soft_shadows = False
                            print(f"Disabled soft shadows for material preview")
                        if hasattr(eevee, 'use_raytrace'):
                            eevee.use_raytrace = False
                            print(f"Disabled raytracing for material preview")
                        if hasattr(eevee, 'use_ssr'):
                            eevee.use_ssr = False
                            print(f"Disabled screen space reflections for material preview")
                        if hasattr(eevee, 'use_ssr_refraction'):
                            eevee.use_ssr_refraction = False
                            print(f"Disabled screen space refractions for material preview")
                            
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
                            
                            # CRITICAL: Always set maximum simplification for material preview
                            if hasattr(scene.render, 'simplify_subdivision'):
                                scene.render.simplify_subdivision = 0
                                print(f"Set maximum subdivision simplification (0) for material preview")
                            if hasattr(scene.render, 'simplify_child_particles'):
                                scene.render.simplify_child_particles = 0
                                print(f"Set maximum particle simplification (0) for material preview")
                            if hasattr(scene.render, 'simplify_volumes'):
                                scene.render.simplify_volumes = 0
                                print(f"Set maximum volume simplification (0) for material preview")
                            if hasattr(scene.render, 'simplify_shadows'):
                                scene.render.simplify_shadows = 0
                                print(f"Set maximum shadow simplification (0) for material preview")
                            if hasattr(scene.render, 'simplify_culling'):
                                scene.render.simplify_culling = True
                                print(f"Enabled culling simplification for material preview")
                                
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
                
                # Configure workbench settings for optimal performance
                scene.display.shading.light = 'STUDIO'
                scene.display.shading.color_type = 'MATERIAL'
                if props.display_mode == 'WIREFRAME':
                        scene.display.shading.type = 'WIREFRAME'
                else:
                        scene.display.shading.type = 'SOLID'
                
                # Disable anti-aliasing for maximum speed in workbench
                # Viewport anti-aliasing
                if hasattr(scene.display, 'render_aa'):
                    scene.display.render_aa = 'OFF'
                # Render anti-aliasing (render passes)
                if hasattr(scene.display.shading, 'render_pass'):
                    scene.display.shading.render_pass = 'COMBINED'
                # Disable any other performance-impacting settings
                if hasattr(scene.display.shading, 'show_cavity'):
                    scene.display.shading.show_cavity = False
                # The show_shadow attribute doesn't exist in Blender 4.4
                # if hasattr(scene.display.shading, 'show_shadow'):
                #     scene.display.shading.show_shadow = False
                if hasattr(scene.display.shading, 'show_object_outline'):
                    scene.display.shading.show_object_outline = False
                if hasattr(scene.display.shading, 'show_specular_highlight'):
                    scene.display.shading.show_specular_highlight = False
                
                # Handle depth of field in Workbench
                if hasattr(scene.display.shading, 'use_dof'):
                    scene.display.shading.use_dof = props.enable_depth_of_field
                    if props.enable_depth_of_field:
                        print(f"Enabled Workbench depth of field")
                    else:
                        print(f"Disabled Workbench depth of field")
                
                print(f"Workbench anti-aliasing disabled for maximum performance")
            
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
            scene.render.ffmpeg.constant_rate_factor = get_ffmpeg_quality(props.video_quality)
            
            # Audio settings
            if props.include_audio:
                scene.render.ffmpeg.audio_codec = props.audio_codec
                scene.render.ffmpeg.audio_bitrate = props.audio_bitrate
            else:
                scene.render.ffmpeg.audio_codec = 'NONE'
            
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
            self.report({'ERROR'}, f"Error saving original settings: {str(e)}")
            print(f"DETAILED ERROR in saving settings: {str(e)}")
            import traceback
            traceback.print_exc()
            # Continue with applying settings even if saving fails
            print(f"Continuing with applying blast settings despite saving error...")
            
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
            
            print(f"Restoring comprehensive settings for engine: {original.get('render_engine', 'unknown')}")
            
            def safe_restore(obj, attr, value):
                """Safely restore attribute"""
                try:
                    if hasattr(obj, attr):
                        setattr(obj, attr, value)
                        return True
                except Exception as e:
                    print(f"Could not restore {attr}: {e}")
                    return False
            
            # SCENE.RENDER - Restore all basic render settings
            scene.render.filepath = original['filepath']
            scene.render.resolution_x = original['resolution_x']
            scene.render.resolution_y = original['resolution_y']
            scene.render.resolution_percentage = original['resolution_percentage']
            safe_restore(scene.render, 'pixel_aspect_x', original.get('pixel_aspect_x', 1.0))
            safe_restore(scene.render, 'pixel_aspect_y', original.get('pixel_aspect_y', 1.0))
            scene.render.use_file_extension = original['use_file_extension']
            scene.render.use_overwrite = original['use_overwrite']
            scene.render.use_placeholder = original['use_placeholder']
            scene.frame_start = original['frame_start']
            scene.frame_end = original['frame_end']
            scene.frame_step = original['frame_step']
            scene.frame_current = original.get('frame_current', 1)
            
            # Film settings
            scene.render.film_transparent = original['film_transparent']
            scene.render.filter_size = original['filter_size']
            
            # Performance settings
            scene.render.use_persistent_data = original['use_persistent_data']
            scene.render.use_simplify = original['use_simplify']
            scene.render.simplify_subdivision = original['simplify_subdivision']
            scene.render.simplify_child_particles = original['simplify_child_particles']
            scene.render.simplify_volumes = original['simplify_volumes']
            safe_restore(scene.render, 'simplify_subdivision_render', original.get('simplify_subdivision_render', 6))
            safe_restore(scene.render, 'simplify_child_particles_render', original.get('simplify_child_particles_render', 1.0))
            safe_restore(scene.render, 'simplify_volumes_render', original.get('simplify_volumes_render', 1.0))
            
            # Motion blur
            scene.render.use_motion_blur = original['use_motion_blur']
            scene.render.motion_blur_shutter = original['motion_blur_shutter']
            safe_restore(scene.render, 'motion_blur_shutter_curve', original.get('motion_blur_shutter_curve', 'AUTO'))
            safe_restore(scene.render, 'rolling_shutter_type', original.get('rolling_shutter_type', 'NONE'))
            safe_restore(scene.render, 'rolling_shutter_duration', original.get('rolling_shutter_duration', 0.1))
            
            # Threading
            scene.render.threads_mode = original['threads_mode']
            scene.render.threads = original['threads']
            
            # Memory and caching
            safe_restore(scene.render, 'tile_x', original.get('tile_x', 64))
            safe_restore(scene.render, 'tile_y', original.get('tile_y', 64))
            safe_restore(scene.render, 'use_save_buffers', original.get('use_save_buffers', False))
            
            # Preview and display
            context.preferences.view.render_display_type = original['display_mode']
            safe_restore(scene.render, 'preview_pixel_size', original.get('preview_pixel_size', 'AUTO'))
            
            # SCENE.RENDER.IMAGE_SETTINGS - Restore image settings
            if 'image_settings' in original:
                img_settings = original['image_settings']
                scene.render.image_settings.file_format = img_settings['file_format']
                scene.render.image_settings.color_mode = img_settings['color_mode']
                scene.render.image_settings.color_depth = img_settings['color_depth']
                scene.render.image_settings.compression = img_settings['compression']
                scene.render.image_settings.quality = img_settings['quality']
                scene.render.image_settings.use_preview = img_settings['use_preview']
                safe_restore(scene.render.image_settings, 'exr_codec', img_settings.get('exr_codec', 'ZIP'))
                safe_restore(scene.render.image_settings, 'use_zbuffer', img_settings.get('use_zbuffer', False))
                safe_restore(scene.render.image_settings, 'jpeg2k_codec', img_settings.get('jpeg2k_codec', 'JP2'))
                safe_restore(scene.render.image_settings, 'tiff_codec', img_settings.get('tiff_codec', 'DEFLATE'))
            
            # Scene/world settings
            scene.use_nodes = original['use_nodes']
            
            # Compositing settings
            scene.render.use_compositing = original['use_compositing']
            scene.render.use_sequencer = original['use_sequencer']
            
            # Border and crop settings
            scene.render.use_border = original['use_border']
            scene.render.border_min_x = original['border_min_x']
            scene.render.border_max_x = original['border_max_x']
            scene.render.border_min_y = original['border_min_y']
            scene.render.border_max_y = original['border_max_y']
            scene.render.use_crop_to_border = original['use_crop_to_border']
            
            # Metadata settings - comprehensive
            scene.render.use_stamp = original['use_stamp']
            scene.render.use_stamp_date = original['use_stamp_date']
            scene.render.use_stamp_time = original['use_stamp_time']
            scene.render.use_stamp_frame = original['use_stamp_frame']
            scene.render.use_stamp_camera = original['use_stamp_camera']
            scene.render.use_stamp_lens = original['use_stamp_lens']
            scene.render.use_stamp_scene = original['use_stamp_scene']
            scene.render.use_stamp_note = original['use_stamp_note']
            scene.render.stamp_note_text = original['stamp_note_text']
            scene.render.use_stamp_marker = original['use_stamp_marker']
            scene.render.use_stamp_filename = original['use_stamp_filename']
            scene.render.use_stamp_render_time = original['use_stamp_render_time']
            scene.render.use_stamp_memory = original['use_stamp_memory']
            scene.render.use_stamp_hostname = original['use_stamp_hostname']
            scene.render.stamp_font_size = original['stamp_font_size']
            scene.render.stamp_foreground = original['stamp_foreground']
            scene.render.stamp_background = original['stamp_background']
            
            # Hair settings
            safe_restore(scene.render, 'hair_type', original.get('hair_type', 'PATH'))
            safe_restore(scene.render, 'hair_subdiv', original.get('hair_subdiv', 3))
            
            # SCENE.RENDER.FFMPEG - Restore FFmpeg settings
            if 'ffmpeg' in original:
                ffmpeg = original['ffmpeg']
                scene.render.ffmpeg.format = ffmpeg['format']
                scene.render.ffmpeg.codec = ffmpeg['codec']
                scene.render.ffmpeg.video_bitrate = ffmpeg['video_bitrate']
                scene.render.ffmpeg.minrate = ffmpeg['minrate']
                scene.render.ffmpeg.maxrate = ffmpeg['maxrate']
                scene.render.ffmpeg.buffersize = ffmpeg['buffersize']
                scene.render.ffmpeg.muxrate = ffmpeg['muxrate']
                scene.render.ffmpeg.packetsize = ffmpeg['packetsize']
                scene.render.ffmpeg.constant_rate_factor = ffmpeg['constant_rate_factor']
                scene.render.ffmpeg.gopsize = ffmpeg['gopsize']
                safe_restore(scene.render.ffmpeg, 'use_max_b_frames', ffmpeg.get('use_max_b_frames', False))
                safe_restore(scene.render.ffmpeg, 'max_b_frames', ffmpeg.get('max_b_frames', 2))
                safe_restore(scene.render.ffmpeg, 'use_autosplit', ffmpeg.get('use_autosplit', False))
                safe_restore(scene.render.ffmpeg, 'autosplit_size', ffmpeg.get('autosplit_size', 2048))
                scene.render.ffmpeg.audio_codec = ffmpeg['audio_codec']
                scene.render.ffmpeg.audio_bitrate = ffmpeg['audio_bitrate']
                scene.render.ffmpeg.audio_channels = ffmpeg['audio_channels']
                scene.render.ffmpeg.audio_mixrate = ffmpeg['audio_mixrate']
                scene.render.ffmpeg.audio_volume = ffmpeg['audio_volume']
            
            # Restore render engine first
            if 'render_engine' in original:
                scene.render.engine = original['render_engine']
                print(f"Restored render engine to: {original['render_engine']}")
                
                # SCENE.CYCLES - Always restore Cycles settings if available  
                print(f"Checking for Cycles settings in saved data...")
                print(f"'cycles' in original: {'cycles' in original}")
                if 'cycles' in original:
                    print(f"original['cycles'] exists: {bool(original['cycles'])}")
                    print(f"original['cycles'] keys: {list(original['cycles'].keys()) if original['cycles'] else 'empty'}")
                else:
                    print(f"ERROR: 'cycles' key not found in original settings! Keys available: {list(original.keys())}")
                
                if 'cycles' in original and original['cycles']:
                    cycles_settings = original['cycles']
                    cycles = scene.cycles
                    print(f"Restoring ALL Cycles settings - samples: {cycles_settings.get('samples', 'unknown')}")
                    
                    # Restore ALL Cycles settings comprehensively
                    cycles.device = cycles_settings['device']
                    safe_restore(cycles, 'feature_set', cycles_settings.get('feature_set', 'SUPPORTED'))
                    safe_restore(cycles, 'shading_system', cycles_settings.get('shading_system', 'SVM'))
                    cycles.samples = cycles_settings['samples']
                    cycles.preview_samples = cycles_settings['preview_samples']
                    safe_restore(cycles, 'aa_samples', cycles_settings.get('aa_samples', 4))
                    safe_restore(cycles, 'preview_aa_samples', cycles_settings.get('preview_aa_samples', 4))
                    cycles.use_denoising = cycles_settings['use_denoising']
                    safe_restore(cycles, 'denoiser', cycles_settings.get('denoiser', 'OPENIMAGEDENOISE'))
                    safe_restore(cycles, 'denoising_input_passes', cycles_settings.get('denoising_input_passes', 'RGB_ALBEDO_NORMAL'))
                    safe_restore(cycles, 'use_denoising_input_passes', cycles_settings.get('use_denoising_input_passes', True))
                    safe_restore(cycles, 'denoising_prefilter', cycles_settings.get('denoising_prefilter', 'ACCURATE'))
                    cycles.use_adaptive_sampling = cycles_settings['use_adaptive_sampling']
                    cycles.adaptive_threshold = cycles_settings['adaptive_threshold']
                    cycles.adaptive_min_samples = cycles_settings['adaptive_min_samples']
                    safe_restore(cycles, 'time_limit', cycles_settings.get('time_limit', 0.0))
                    safe_restore(cycles, 'use_preview_adaptive_sampling', cycles_settings.get('use_preview_adaptive_sampling', False))
                    safe_restore(cycles, 'preview_adaptive_threshold', cycles_settings.get('preview_adaptive_threshold', 0.1))
                    safe_restore(cycles, 'preview_adaptive_min_samples', cycles_settings.get('preview_adaptive_min_samples', 0))
                    safe_restore(cycles, 'seed', cycles_settings.get('seed', 0))
                    safe_restore(cycles, 'use_animated_seed', cycles_settings.get('use_animated_seed', False))
                    safe_restore(cycles, 'sample_clamp_direct', cycles_settings.get('sample_clamp_direct', 0.0))
                    safe_restore(cycles, 'sample_clamp_indirect', cycles_settings.get('sample_clamp_indirect', 0.0))
                    cycles.light_sampling_threshold = cycles_settings['light_sampling_threshold']
                    safe_restore(cycles, 'sample_all_lights_direct', cycles_settings.get('sample_all_lights_direct', True))
                    safe_restore(cycles, 'sample_all_lights_indirect', cycles_settings.get('sample_all_lights_indirect', True))
                    cycles.max_bounces = cycles_settings['max_bounces']
                    cycles.diffuse_bounces = cycles_settings['diffuse_bounces']
                    cycles.glossy_bounces = cycles_settings['glossy_bounces']
                    cycles.transmission_bounces = cycles_settings['transmission_bounces']
                    cycles.volume_bounces = cycles_settings['volume_bounces']
                    safe_restore(cycles, 'transparent_max_bounces', cycles_settings.get('transparent_max_bounces', 8))
                    cycles.caustics_reflective = cycles_settings['caustics_reflective']
                    cycles.caustics_refractive = cycles_settings['caustics_refractive']
                    safe_restore(cycles, 'filter_type', cycles_settings.get('filter_type', 'GAUSSIAN'))
                    safe_restore(cycles, 'filter_width', cycles_settings.get('filter_width', 1.5))
                    cycles.pixel_filter_width = cycles_settings['pixel_filter_width']
                    cycles.use_persistent_data = cycles_settings['use_persistent_data']
                    safe_restore(cycles, 'debug_use_spatial_splits', cycles_settings.get('debug_use_spatial_splits', False))
                    safe_restore(cycles, 'debug_use_hair_bvh', cycles_settings.get('debug_use_hair_bvh', True))
                    safe_restore(cycles, 'debug_bvh_type', cycles_settings.get('debug_bvh_type', 'DYNAMIC_BVH'))
                    safe_restore(cycles, 'debug_use_compact_bvh', cycles_settings.get('debug_use_compact_bvh', True))
                    safe_restore(cycles, 'tile_size', cycles_settings.get('tile_size', 256))
                    safe_restore(cycles, 'use_auto_tile', cycles_settings.get('use_auto_tile', False))
                    safe_restore(cycles, 'progressive', cycles_settings.get('progressive', 'PATH'))
                    safe_restore(cycles, 'use_square_samples', cycles_settings.get('use_square_samples', False))
                    safe_restore(cycles, 'blur_glossy', cycles_settings.get('blur_glossy', 0.0))
                    safe_restore(cycles, 'use_transparent_shadows', cycles_settings.get('use_transparent_shadows', True))
                    safe_restore(cycles, 'volume_step_rate', cycles_settings.get('volume_step_rate', 1.0))
                    safe_restore(cycles, 'volume_preview_step_rate', cycles_settings.get('volume_preview_step_rate', 1.0))
                    safe_restore(cycles, 'volume_max_steps', cycles_settings.get('volume_max_steps', 1024))
                    
                    print(f"ALL Cycles settings restoration completed")
                    
                # SCENE.EEVEE - Always restore EEVEE settings if available
                if 'eevee' in original and original['eevee']:
                    eevee_settings = original['eevee']
                    eevee_attr = 'eevee' if hasattr(scene, 'eevee') else 'eevee_next'
                    eevee = getattr(scene, eevee_attr) if hasattr(scene, eevee_attr) else None
                    if eevee:
                        print(f"Restoring ALL EEVEE settings - samples: {eevee_settings.get('taa_render_samples', 'unknown')}")
                        
                        # Restore ALL EEVEE settings comprehensively
                        safe_restore(eevee, 'taa_render_samples', eevee_settings.get('taa_render_samples', 64))
                        safe_restore(eevee, 'taa_samples', eevee_settings.get('taa_samples', 16))
                        safe_restore(eevee, 'use_bloom', eevee_settings.get('use_bloom', False))
                        safe_restore(eevee, 'bloom_threshold', eevee_settings.get('bloom_threshold', 0.8))
                        safe_restore(eevee, 'bloom_knee', eevee_settings.get('bloom_knee', 0.5))
                        safe_restore(eevee, 'bloom_radius', eevee_settings.get('bloom_radius', 6.5))
                        safe_restore(eevee, 'bloom_intensity', eevee_settings.get('bloom_intensity', 0.05))
                        safe_restore(eevee, 'use_ssr', eevee_settings.get('use_ssr', False))
                        safe_restore(eevee, 'use_ssr_refraction', eevee_settings.get('use_ssr_refraction', False))
                        safe_restore(eevee, 'ssr_max_roughness', eevee_settings.get('ssr_max_roughness', 0.5))
                        safe_restore(eevee, 'ssr_thickness', eevee_settings.get('ssr_thickness', 0.2))
                        safe_restore(eevee, 'ssr_border_fade', eevee_settings.get('ssr_border_fade', 0.075))
                        safe_restore(eevee, 'ssr_firefly_fac', eevee_settings.get('ssr_firefly_fac', 10.0))
                        safe_restore(eevee, 'use_motion_blur', eevee_settings.get('use_motion_blur', False))
                        safe_restore(eevee, 'motion_blur_samples', eevee_settings.get('motion_blur_samples', 8))
                        safe_restore(eevee, 'motion_blur_shutter', eevee_settings.get('motion_blur_shutter', 0.5))
                        safe_restore(eevee, 'use_volumetric_lights', eevee_settings.get('use_volumetric_lights', False))
                        safe_restore(eevee, 'volumetric_start', eevee_settings.get('volumetric_start', 0.1))
                        safe_restore(eevee, 'volumetric_end', eevee_settings.get('volumetric_end', 100.0))
                        safe_restore(eevee, 'volumetric_tile_size', eevee_settings.get('volumetric_tile_size', '8'))
                        safe_restore(eevee, 'volumetric_samples', eevee_settings.get('volumetric_samples', 64))
                        safe_restore(eevee, 'volumetric_sample_distribution', eevee_settings.get('volumetric_sample_distribution', 0.8))
                        safe_restore(eevee, 'use_volumetric_shadows', eevee_settings.get('use_volumetric_shadows', False))
                        safe_restore(eevee, 'volumetric_shadow_samples', eevee_settings.get('volumetric_shadow_samples', 16))
                        safe_restore(eevee, 'gi_diffuse_bounces', eevee_settings.get('gi_diffuse_bounces', 3))
                        safe_restore(eevee, 'gi_cubemap_resolution', eevee_settings.get('gi_cubemap_resolution', '512'))
                        safe_restore(eevee, 'gi_visibility_resolution', eevee_settings.get('gi_visibility_resolution', '16'))
                        safe_restore(eevee, 'gi_irradiance_smoothing', eevee_settings.get('gi_irradiance_smoothing', 0.1))
                        safe_restore(eevee, 'gi_glossy_clamp', eevee_settings.get('gi_glossy_clamp', 0.0))
                        safe_restore(eevee, 'gi_filter_quality', eevee_settings.get('gi_filter_quality', 1.0))
                        safe_restore(eevee, 'use_persistent_data', eevee_settings.get('use_persistent_data', False))
                        safe_restore(eevee, 'shadow_cube_size', eevee_settings.get('shadow_cube_size', '512'))
                        safe_restore(eevee, 'shadow_cascade_size', eevee_settings.get('shadow_cascade_size', '1024'))
                        safe_restore(eevee, 'use_shadow_high_bitdepth', eevee_settings.get('use_shadow_high_bitdepth', False))
                        safe_restore(eevee, 'use_soft_shadows', eevee_settings.get('use_soft_shadows', True))
                        safe_restore(eevee, 'use_shadows', eevee_settings.get('use_shadows', True))
                        safe_restore(eevee, 'light_threshold', eevee_settings.get('light_threshold', 0.01))
                        safe_restore(eevee, 'use_gtao', eevee_settings.get('use_gtao', False))
                        safe_restore(eevee, 'gtao_distance', eevee_settings.get('gtao_distance', 0.2))
                        safe_restore(eevee, 'gtao_factor', eevee_settings.get('gtao_factor', 1.0))
                        safe_restore(eevee, 'gtao_quality', eevee_settings.get('gtao_quality', 0.25))
                        safe_restore(eevee, 'use_overscan', eevee_settings.get('use_overscan', False))
                        safe_restore(eevee, 'overscan_size', eevee_settings.get('overscan_size', 3.0))
                        safe_restore(eevee, 'shadow_ray_count', eevee_settings.get('shadow_ray_count', 1))
                        safe_restore(eevee, 'shadow_step_count', eevee_settings.get('shadow_step_count', 6))
                        safe_restore(eevee, 'fast_gi_method', eevee_settings.get('fast_gi_method', 'GLOBAL_ILLUMINATION'))
                        safe_restore(eevee, 'fast_gi_ray_count', eevee_settings.get('fast_gi_ray_count', 4))
                        safe_restore(eevee, 'fast_gi_step_count', eevee_settings.get('fast_gi_step_count', 4))
                        safe_restore(eevee, 'fast_gi_quality', eevee_settings.get('fast_gi_quality', 0.25))
                        safe_restore(eevee, 'fast_gi_distance', eevee_settings.get('fast_gi_distance', 10.0))
                        
                        print(f"ALL EEVEE settings restoration completed")
                            
                # SCENE.DISPLAY (WORKBENCH) - Always restore Workbench settings if available  
                if 'workbench' in original and original['workbench']:
                    workbench_settings = original['workbench']
                    print(f"Restoring ALL Workbench settings")
                    
                    # Restore ALL Workbench settings comprehensively
                    scene.display.shading.type = workbench_settings['shading_type']
                    scene.display.shading.light = workbench_settings['light']
                    scene.display.shading.color_type = workbench_settings['color_type']
                    safe_restore(scene.display.shading, 'single_color', workbench_settings.get('single_color', (0.8, 0.8, 0.8)))
                    safe_restore(scene.display.shading, 'background_type', workbench_settings.get('background_type', 'THEME'))
                    safe_restore(scene.display.shading, 'background_color', workbench_settings.get('background_color', (0.05, 0.05, 0.05)))
                    safe_restore(scene.display.shading, 'cavity_ridge_factor', workbench_settings.get('cavity_ridge_factor', 1.0))
                    safe_restore(scene.display.shading, 'cavity_valley_factor', workbench_settings.get('cavity_valley_factor', 1.0))
                    safe_restore(scene.display.shading, 'curvature_ridge_factor', workbench_settings.get('curvature_ridge_factor', 1.0))
                    safe_restore(scene.display.shading, 'curvature_valley_factor', workbench_settings.get('curvature_valley_factor', 1.0))
                    safe_restore(scene.display, 'render_aa', workbench_settings.get('render_aa', 'FXAA'))
                    safe_restore(scene.display.shading, 'show_cavity', workbench_settings.get('show_cavity', False))
                    safe_restore(scene.display.shading, 'show_object_outline', workbench_settings.get('show_object_outline', False))
                    safe_restore(scene.display.shading, 'show_specular_highlight', workbench_settings.get('show_specular_highlight', True))
                    safe_restore(scene.display.shading, 'use_dof', workbench_settings.get('use_dof', False))
                    safe_restore(scene.display.shading, 'show_xray', workbench_settings.get('show_xray', False))
                    safe_restore(scene.display.shading, 'xray_alpha', workbench_settings.get('xray_alpha', 0.5))
                    safe_restore(scene.display.shading, 'show_shadows', workbench_settings.get('show_shadows', False))
                    safe_restore(scene.display.shading, 'shadow_intensity', workbench_settings.get('shadow_intensity', 0.5))
                    safe_restore(scene.display.shading, 'studio_light', workbench_settings.get('studio_light', 'DEFAULT'))
                    safe_restore(scene.display.shading, 'studiolight_rotate_z', workbench_settings.get('studiolight_rotate_z', 0.0))
                    safe_restore(scene.display.shading, 'studiolight_intensity', workbench_settings.get('studiolight_intensity', 1.0))
                    safe_restore(scene.display.shading, 'studiolight_background_alpha', workbench_settings.get('studiolight_background_alpha', 0.0))
                    safe_restore(scene.display.shading, 'studiolight_background_blur', workbench_settings.get('studiolight_background_blur', 0.0))
                    
                    print(f"ALL Workbench settings restoration completed")
                
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
        layout = self.layout
        scene = context.scene
        props = scene.basedplayblast
        
        # Main buttons - now integrated with output settings
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("bpl.create_playblast", text="PLAYBLAST", icon='RENDER_ANIMATION')
        row.operator("bpl.view_playblast", text="VIEW", icon='PLAY')
        
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
        
        # Properties - single collapsible section
        props_box = layout.box()
        row = props_box.row(align=True)
        row.prop(context.scene, "basedplayblast_show_properties", icon="TRIA_DOWN" if context.scene.get("basedplayblast_show_properties", False) else "TRIA_RIGHT", icon_only=True, emboss=False)
        row.label(text="Properties")
        row.operator("bpl.apply_user_defaults", text="", icon='PREFERENCES')
        
        if context.scene.get("basedplayblast_show_properties", False):
            # 1. Display Mode
            display_box = props_box.box()
            display_box.label(text="Display Mode", icon='SHADING_RENDERED')
            col = display_box.column(align=True)
            col.prop(props, "display_mode", text="")
            col.prop(props, "auto_disable_overlays")
            col.prop(props, "enable_depth_of_field")
            
            # 2. Frame Range
            frame_range_box = props_box.box()
            frame_range_box.label(text="Frame Range", icon='TIME')
            col = frame_range_box.column(align=True)
            col.prop(props, "use_scene_frame_range")
            
            if not props.use_scene_frame_range:
                row = col.row(align=True)
                row.prop(props, "start_frame")
                row.prop(props, "end_frame")
            
            # 3. Resolution
            resolution_box = props_box.box()
            resolution_box.label(text="Resolution", icon='TEXTURE')
            col = resolution_box.column(align=True)
            col.prop(props, "resolution_mode", text="")
            
            if props.resolution_mode == 'PRESET':
                col.prop(props, "resolution_preset", text="")
            elif props.resolution_mode == 'CUSTOM':
                row = col.row(align=True)
                row.prop(props, "resolution_x")
                row.prop(props, "resolution_y")
            
            col.prop(props, "resolution_percentage")
            
            # 4. Format
            format_box = props_box.box()
            format_box.label(text="Format", icon='FILE_MOVIE')
            col = format_box.column(align=True)
            col.prop(props, "video_format", text="")
            col.prop(props, "video_codec", text="")
            
            # Custom FFmpeg arguments
            col.prop(props, "use_custom_ffmpeg_args")
            if props.use_custom_ffmpeg_args:
                col.prop(props, "custom_ffmpeg_args", text="")
            else:
                col.prop(props, "video_quality", text="")
            
            col.prop(props, "include_audio")
            if props.include_audio:
                row = col.row(align=True)
                row.prop(props, "audio_codec", text="")
                row.prop(props, "audio_bitrate")
            
            # 5. Metadata
            metadata_box = props_box.box()
            metadata_box.label(text="Metadata", icon='TEXT')
            col = metadata_box.column(align=True)
            col.prop(props, "show_metadata", text="Show Metadata")
            
            if props.show_metadata:
                col.prop(props, "metadata_note", text="")
                
                row = col.row(align=True)
                row.prop(props, "metadata_date", toggle=True)
                row.prop(props, "metadata_frame", toggle=True)
                row.prop(props, "metadata_scene", toggle=True)
                
                row = col.row(align=True)
                row.prop(props, "metadata_camera", toggle=True)
                row.prop(props, "metadata_lens", toggle=True)
                row.prop(props, "metadata_resolution", toggle=True)

# Define the addon preferences class
class BPL_AddonPreferences(AddonPreferences):
    bl_idname = __name__
    
    default_video_quality: EnumProperty(
        name="Default Video Quality",
        description="Default quality setting for the add-on. This will be applied on file load.",
        items=VIDEO_QUALITY_ITEMS,
        default='PERC_LOSSLESS'
    )

    default_use_custom_ffmpeg_args: BoolProperty(
        name="Enable Custom FFmpeg By Default",
        description="Sets the default state for 'Use Custom FFmpeg Args' when applying user defaults.",
        default=False
    )

    default_ffmpeg_args: StringProperty(
        name="Default FFmpeg Arguments",
        description="Default custom FFmpeg arguments for advanced users.",
        default="-c:v h264_nvenc -preset fast -crf 0"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="BasedPlayblast User Defaults")
        box = layout.box()
        box.prop(self, "default_video_quality")
        box.prop(self, "default_use_custom_ffmpeg_args")
        box.prop(self, "default_ffmpeg_args")

def on_load_post(dummy):
    """Applies user defaults after a file is loaded."""
    # Using a timer ensures that the context is correct
    def apply_defaults():
        try:
            bpy.ops.bpl.apply_user_defaults('EXEC_DEFAULT')
        except Exception as e:
            # This can fail if the operator is not ready, so fail silently
            print(f"BasedPlayblast: Could not apply user defaults on load: {e}")
    bpy.app.timers.register(apply_defaults, first_interval=0.1)

# Registration
classes = (
    BPLProperties,
    BPL_OT_create_playblast,
    BPL_OT_view_playblast,
    BPL_OT_view_latest_playblast,
    BPL_OT_sync_output_path,
    BPL_OT_sync_file_name,
    BPL_OT_apply_user_defaults,
    BPL_OT_apply_blast_settings,
    BPL_OT_restore_original_settings,
    BPL_PT_main_panel,
    BPL_AddonPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.basedplayblast = PointerProperty(type=BPLProperties)
    
    # Register property for collapsible properties section
    bpy.types.Scene.basedplayblast_show_properties = BoolProperty(
        name="Show Properties",
        default=False
    )
    bpy.app.handlers.load_post.append(on_load_post)

def unregister():
    bpy.app.handlers.load_post.remove(on_load_post)
    # Unregister property for collapsible properties section
    del bpy.types.Scene.basedplayblast_show_properties
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.basedplayblast

if __name__ == "__main__":
    register()