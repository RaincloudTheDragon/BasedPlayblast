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

# v0.3.3
    - Apply blast settings:
        - Set eevee render defaults to be even lower
        - No longer changes viewport mode or moves the camera
    - Restore original settings now fully restores ALL render settings. So you can save over without a second thought.
    - Default ffmpeg option set to Lossless