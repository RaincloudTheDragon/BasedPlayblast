# BasedPlayblast

A simple "fork" of [this plugin](https://blenderartists.org/t/free-playblast-addon/1450365) that simplifies its functions and tailors them in a more sophisticated manner.

BasedPlayblast lets you quickly create playblasts from Blender without the headache of reconfiguring your render settings or using render presets. It's perfect for previewing animations, showing WIPs to clients, or just checking how your stuff looks in motion. It's like rendering your viewport. Actually, that's exactly what it is...

## Main support for 4.4; 4.3 and earlier may still work, but don't expect perfect behavior, at least not yet.

## Features

- Streamlined settings - just name your output, or reuse your render output with the 'blast_' prefix.
- Live progress tracking that actually works (new in v0.2.0!)
- Viewport preview display options (wireframe, solid, material, rendered)
- Metadata options for including frame numbers, camera info, and custom notes
- Auto-plays your video (externally) when it's done
- Saves your playblast settings between sessions
- Automatic update checking and one-click updates from GitHub releases

## How to install

1. Download the latest release
2. Click and drag .zip into blender, or go to Edit > Preferences > Add-ons > Install that way
3. Enable the addon by checking the box

## Usage

1. Find the BasedPlayblast panel in the Properties > Output tab
2. Pick your output settings (resolution, format, custom ffmpeg args, etc.)
3. Hit that big "Create Playblast" button
4. Watch as your animation renders with a progress bar that actually works!
5. The video will auto-play when it's done

## Flamenco
You can now farm a blast! This requires both the plugin, and Flamenco to work together.

1. Place BasedPlayblast.js in /Flamenco/scripts - this script is just for outputting the blast, and is, thus, destructive. Do not use this for anything except playblasts.
2. Set output settings within BasedPlayblast panel
3. Click "Apply Blast Render Settings" - this takes the settings that the blaster normally handles locally, and puts it into the blendfile so it can be farmed.
4. Set flamenco settings (I recommend # of frames/# of workers)
5. Click "Restore Original Render Settings" - you probably don't want to keep it on the blast settings permanently...

### Updating the addon

The addon will automatically check for updates when Blender starts. You can also:

1. Go to Edit > Preferences > Add-ons
2. Find BasedPlayblast in the list
3. In the addon preferences, click "Check Now" to check for updates
4. If an update is available, click "Install Update" to download and install it

## Planned features:

- Configurable settings so defaults can be set by end user (default prefix, etc)
- sequencer audio/video strips support

## Feel free to report bugs