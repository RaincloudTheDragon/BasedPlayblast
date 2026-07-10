# v2.8.0 2026-07-10
    - UI overhaul: quick-setting rows (shading, audio, metadata), Properties layout, default output toggle, optional Flamenco button
    - Flamenco script deployer: pick Manager directory, validate `flamenco-manager.yaml`, copy scripts to `scripts/`
    - UI: separator between action buttons and quick settings

# v2.7.1 2026-07-10
    - Default audio codec MP3 (#14); configurable in add-on preferences

# v2.7.0 2026-07-09
    - **Send to Flamenco** operator: BATv2-safe apply → submit → restore; blend re-save on Blender 5.1+ only; Advanced panel for manual apply/restore
    - **Set from blend file** button: sync output path and filename from the saved `.blend`
    - AV1/NVENC encode fix: VBR + CQ 0 (not `constqp -cq 0`); uncapped when bitrate limit is 0
    - FFmpeg accessibility: addon-bundled binary with bootstrap download; fallbacks avoid Chocolatey PATH
    - Encode defaults (#13): NVENC VBR + CQ 0, encode speed + optional bitrate cap; removed quality presets
    - Local temp frames (#11): intermediate PNGs in system temp, cleaned up after encode
    - Flamenco 3.9 job scripts (#12): `py_render_settings`, forward-slash cleanup paths
    - Default Flamenco script deploy path: `F:\software\Flamenco\scripts`

# v2.6.3 2026-02-02
    - Bugfix: fix ffmpeg inaccessibility by adding fallbacks and a preference

# v2.6.2 2026-01-03
    - Bugfix:
        - Fixed PNG compression not being restored after playblast completion (#9)
        - Added safe compression handling to prevent crashes when accessing unsupported formats

# v2.6.1 2025-12-09
    - Bugfix:
        - Fixed premature video conversion triggering before all frames completed
        - Fixed FFmpeg frame pattern for non-zero starting frames (added -start_number parameter)

# v2.6.0 2025-12-02
    - Added comprehensive audio support (#7)
        - Audio detection for sequencer strips
        - Automatic sequencer enablement when audio is included
        - Audio extraction and encoding for PNG-to-video path
        - Warning when audio is enabled but no audio strips are found
        - Support for all audio sources (sequencer strips, scene sound strips)

# v2.5.0 2025-12-02
    - Expanded compatibility to Blender 4.2 LTS, 4.5 LTS, and 5.0+ (#8)
    - Fixed blast completion detection (#5)
    - Blender 5.0 video format handling changed, use PNG as efficient workaround

# v2.4.0 2025-12-02
    - Added repo bootstrap to ensure Rainy's Extensions Repo is present
    - Minimum version Blender 4.2 LTS for #8 

# v2.3.1 2025-12-01
    - Fix version mismatch in manifest.

# v2.3.0 2025-11-26
    - Support Blender 5.0
    - Potential fix to #5

# v1.2.0 2025-09-18
    - Flamenco: enforce PNG (15% compression) and respect resolution percentage.
        - Updated job scripts for CPU/GPU; deployment now targets Flamenco 3.7 and copies both scripts.
    - Apply Blast Render Settings (Cycles): always enable persistent data; disable tiling for faster renders.

# v1.1.1 2025-06-27
    - Bugfixes
        - Local blast: fixed main operator accidentally setting dimensions to 1280x720 and frame range to 1-250 regardless of what was previously set.

# v1.1.0 2025-06-23
    - Bugfixes
        - Local blast: Fixed default encoding option resulting in broken video file on some systems by replacing the default with Perceptually lossless instead of Lossless
        - Local Blast: fixed not appending frame range to end of output name
    - Features
        - Added user default preferences for ffmpeg arguments and encoding preset. Addon preferences can be found in the Add-ons menu in Preferences.

# v1.0.0 2025-06-23
    - Upgraded to Blender Extension platform
    - Added comprehensive render settings storage and restoration
    - Improved EEVEE raytracing optimization for maximum performance
    - Enhanced material preview mode with automatic studio lighting
    - Fixed various render engine compatibility issues

# v0.3.3 2025-06-05
- Apply blast settings:
    - Set eevee render defaults to be even lower
    - No longer changes viewport mode or moves the camera
- Restore original settings now fully restores ALL render settings. So you can save over without a second thought.
- Default ffmpeg option set to Lossless

# v0.3.2 2025-05-12
- added keep frames option in case of corruption
- workbench settings optimization for apply blast render settings
    - DOF option support

# v0.3.1 2025-05-07
    - Properly integrated material and rendered playblasts with Flamenco.

# v0.3.0 2025-05-07
    - Added Flamenco integration.
    - Replaced auto-updater with CGCookie's module.

# v0.2.4 2025-04-21
    - Fixed tuple traceback on 4.3 by setting minimum version to 4.3.

# v0.2.3 2025-04-17
    - Attempted fix for playblast hanging, still broken in some circumstances.
    - Added Updater in addon preferences
    - Fixed manual scene range

# v0.3.0 2025-05-07
    - Added Flamenco integration
    - Integrated CGCookie/blender-addon-updater to replace mine
    - Flamenco job: Switched to JPG for fastest saving   

# v0.3.1 2025-05-07
    - fixed Flamenco integration for material/rendered preview blasts

# Release v1.0.0 2025-06-23
    - Apply blast settings:
        - Set eevee render defaults to be even lower
        - No longer changes viewport mode or moves the camera
    - Restore original settings now fully restores ALL render settings. So you can save over without a second thought.
    - Default ffmpeg option set to Lossless
    - Local Blast:
        - Now supports audio! It's off by default, but so long as you have audio in your scene, it will be in the render result.
        - Fixed Rendered Cycles blasts yielding a black screen.

# v1.1.0 2025-06-23
    - Bugfixes
        - Local blast: Fixed default encoding option resulting in broken video file on some systems by replacing the default with Perceptually lossless instead of Lossless
        - Local Blast: fixed not appending frame range to end of output name
    - Features
        - Added user default preferences for ffmpeg arguments and encoding preset. Addon preferences can be found in the Add-ons menu in Preferences.

# v1.1.1 2025-06-27
    - Bugfixes
        - Local blast: fixed main operator accidentally setting dimensions to 1280x720 and frame range to 1-250 regardless of what was previously set.

# v1.2.0 2025-09-18
    - Flamenco: enforce PNG (15% compression) and respect resolution percentage.
        - Updated job scripts for CPU/GPU; deployment now targets Flamenco 3.7 and copies both scripts.
    - Apply Blast Render Settings (Cycles): always enable persistent data; disable tiling for faster renders.

# v1.3.0 2025-11-18
    - Updated to support Blender 5.0.0!