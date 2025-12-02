# v2.4.0 2025-12-02
    - Added repo bootstrap to ensure Rainy's Extensions Repo is present
    - Minimum version Blender 4.2 LTS for #8 

# v2.3.1
    - Fix version mismatch in manifest.

# v2.3.0
    - Support Blender 5.0
    - Potential fix to #5

# v1.2.0
    - Flamenco: enforce PNG (15% compression) and respect resolution percentage.
        - Updated job scripts for CPU/GPU; deployment now targets Flamenco 3.7 and copies both scripts.
    - Apply Blast Render Settings (Cycles): always enable persistent data; disable tiling for faster renders.

# v1.1.1
    - Bugfixes
        - Local blast: fixed main operator accidentally setting dimensions to 1280x720 and frame range to 1-250 regardless of what was previously set.

# v1.1.0
    - Bugfixes
        - Local blast: Fixed default encoding option resulting in broken video file on some systems by replacing the default with Perceptually lossless instead of Lossless
        - Local Blast: fixed not appending frame range to end of output name
    - Features
        - Added user default preferences for ffmpeg arguments and encoding preset. Addon preferences can be found in the Add-ons menu in Preferences.

# v1.0.0
    - Upgraded to Blender Extension platform
    - Added comprehensive render settings storage and restoration
    - Improved EEVEE raytracing optimization for maximum performance
    - Enhanced material preview mode with automatic studio lighting
    - Fixed various render engine compatibility issues

# v0.3.3
- Apply blast settings:
    - Set eevee render defaults to be even lower
    - No longer changes viewport mode or moves the camera
- Restore original settings now fully restores ALL render settings. So you can save over without a second thought.
- Default ffmpeg option set to Lossless

# v0.3.2
- added keep frames option in case of corruption
- workbench settings optimization for apply blast render settings
    - DOF option support

# v0.3.1
    - Properly integrated material and rendered playblasts with Flamenco.

# v0.3.0
    - Added Flamenco integration.
    - Replaced auto-updater with CGCookie's module.

# v0.2.4 2025-04-21
    - Fixed tuple traceback on 4.3 by setting minimum version to 4.3.

# v0.2.3
    - Attempted fix for playblast hanging, still broken in some circumstances.
    - Added Updater in addon preferences
    - Fixed manual scene range

# v0.3.0
    - Added Flamenco integration
    - Integrated CGCookie/blender-addon-updater to replace mine
    - Flamenco job: Switched to JPG for fastest saving   

# v0.3.1
    - fixed Flamenco integration for material/rendered preview blasts

# Release v1.0.0
    - Apply blast settings:
        - Set eevee render defaults to be even lower
        - No longer changes viewport mode or moves the camera
    - Restore original settings now fully restores ALL render settings. So you can save over without a second thought.
    - Default ffmpeg option set to Lossless
    - Local Blast:
        - Now supports audio! It's off by default, but so long as you have audio in your scene, it will be in the render result.
        - Fixed Rendered Cycles blasts yielding a black screen.

# v1.1.0
    - Bugfixes
        - Local blast: Fixed default encoding option resulting in broken video file on some systems by replacing the default with Perceptually lossless instead of Lossless
        - Local Blast: fixed not appending frame range to end of output name
    - Features
        - Added user default preferences for ffmpeg arguments and encoding preset. Addon preferences can be found in the Add-ons menu in Preferences.

# v1.1.1
    - Bugfixes
        - Local blast: fixed main operator accidentally setting dimensions to 1280x720 and frame range to 1-250 regardless of what was previously set.

# v1.2.0
    - Flamenco: enforce PNG (15% compression) and respect resolution percentage.
        - Updated job scripts for CPU/GPU; deployment now targets Flamenco 3.7 and copies both scripts.
    - Apply Blast Render Settings (Cycles): always enable persistent data; disable tiling for faster renders.

# v1.3.0
    - Updated to support Blender 5.0.0!