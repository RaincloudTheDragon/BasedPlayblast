# BasedPlayblast

A simple "fork" of [this plugin](https://blenderartists.org/t/free-playblast-addon/1450365) that simplifies its functions and tailors them in a more sophisticated manner.

BasedPlayblast lets you quickly create playblasts from Blender without the headache of reconfiguring your render settings or using render presets. It's perfect for previewing animations, showing WIPs to clients, or just checking how your stuff looks in motion. It's like rendering your viewport. Actually, that's exactly what it is...

## Officially supports Blender 4.4.0, but probably still compatible with 4.3.2 or other previous versions.

## Features

- Streamlined settings - just name your output, or reuse your render output with the 'blast_' prefix.
- Live progress tracking that actually works (new in v0.2.0!)
- Viewport preview display options (wireframe, solid, material, rendered)
- Metadata options for including frame numbers, camera info, and custom notes
- Auto-plays your video (externally) when it's done
- Saves your playblast settings between sessions

## How to install

1. Download the latest release
2. Click and drag .zip into blender, or go to Edit > Preferences > Add-ons > Install that way
3. Enable the addon by checking the box

## How to use

1. Find the BasedPlayblast panel in the Properties > Output tab
2. Pick your output settings (resolution, format, custom ffmpeg args, etc.)
3. Hit that big "Create Playblast" button
4. Watch as your animation renders with a progress bar that actually works!
5. The video will auto-play when it's done

## What's new in v0.2.0

- No more hanging on playblast
- New progress bar
- 3D viewports now update during playblast and can be interacted with
- Added proper metadata support with custom notes
- Overall more stable and reliable

## Planned features:

- Configurable settings so defaults can be set by end user (default prefix, etc)

## Feel free to report bugs