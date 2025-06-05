# BasedPlayblast

**Easily create playblasts from Blender**

BasedPlayblast is a Blender addon that streamlines the process of creating video playblasts for animation review. It provides optimized render settings for fast preview generation while maintaining visual quality suitable for review purposes.

## Features

- **Fast Playblast Creation**: Optimized render settings for different preview modes (Solid, Material, Rendered)
- **Multiple Display Modes**: Support for Wireframe, Solid, Material Preview, and Rendered modes
- **Flexible Resolution**: Scene, preset, or custom resolution options
- **Video Format Support**: MP4, MOV, AVI, MKV with various codecs (H.264, H.265, AV1, etc.)
- **Metadata Integration**: Automatic inclusion of frame numbers, camera info, and custom notes
- **Settings Management**: Apply and restore render settings without losing your project configuration
- **Flamenco Support**: Custom Flamenco Job Script with a simple, non-destructive workflow

## Installation

### Via BlenderKit's Extension Repository (Recommended)
1. Open Blender (4.3+)
2. Install BlenderKit via https://www.blenderkit.com/get-blenderkit/
3. Open Preferences (Ctrl + ,)
4. Go to **Edit > Preferences > Get Extensions**
5. Search for "BasedPlayblast"
6. Click **Install**
7. Enjoy automatic updating!

### Manual Installation
1. Download the latest release
2. In Blender, go to **Edit > Preferences > Add-ons**
3. Click **Install from Disk** and select the downloaded file
4. Enable the addon in the list

## Usage

1. **Locate the Panel**: Go to **Properties > Output > BasedPlayblast**
2. **Configure Settings**: Set your output path, resolution, and display mode
3. **Create Playblast**: Click the **PLAYBLAST** button
4. **View Result**: Click **VIEW** to open the generated video

- **Apply Blast Settings**: Use this button to apply optimized render settings without rendering
    - Intended particularly for Flamenco. Apply, check the resultant render settings to ensure they're correct, then send to Flamenco using the BasedPlayblast custom Job type.
- **Restore Original Settings**: Return to your original render configuration
- **Display Modes**:
    - **Wireframe/Solid**
        - Fast workbench viewport rendering. Recommended for short and/or locally-blasted projects.
    - **Material**
    - **Rendered**

## Requirements

- Blender 4.3.0 or higher
- Python 3.x (included with Blender)

## Support

- **Documentation**: [GitHub Repository](https://github.com/RaincloudTheDragon/BasedPlayblast)
- **Issues**: Report bugs or request features on GitHub
- **License**: GPL-3.0-or-later

## Changelog

### Version 0.3.3
- Added comprehensive render settings storage and restoration
- Improved EEVEE raytracing optimization for maximum performance
- Enhanced material preview mode with automatic studio lighting
- Fixed various render engine compatibility issues
