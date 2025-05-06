// SPDX-License-Identifier: GPL-3.0-or-later

const JOB_TYPE = {
    label: "BasedPlayblast",
    description: "Create a viewport preview/playblast and generate a video file",
    settings: [
        // Settings for artists to determine:
        { key: "frames", type: "string", required: true,
          eval: "f'{C.scene.frame_start}-{C.scene.frame_end}'",
          evalInfo: {
            showLinkButton: true,
            description: "Scene frame range",
          },
          description: "Frame range to playblast. Examples: '47', '1-30', '3, 5-10, 47-327'" },
        { key: "chunk_size", type: "int32", default: 5, description: "Number of frames to playblast in one Blender task",
          visible: "submission" },

        // playblast_output_root + add_path_components determine the value of playblast_output_path.
        { key: "playblast_output_root", type: "string", subtype: "dir_path", required: true, visible: "submission",
          description: "Base directory of where playblast output is stored. Will have some job-specific parts appended to it"},
        { key: "add_path_components", type: "int32", required: true, default: 0, propargs: {min: 0, max: 32}, visible: "submission",
          description: "Number of path components of the current blend file to use in the playblast output path"},
        { key: "playblast_output_path", type: "string", subtype: "file_path", editable: false,
          eval: "str(Path(abspath(settings.playblast_output_root), last_n_dir_parts(settings.add_path_components), 'blast', jobname, jobname + '_######'))",
          description: "Final file path of where playblast output will be saved"},
          
        // Playblast specific settings
        { key: "resolution_percentage", type: "int32", default: 100, propargs: {min: 1, max: 100}, visible: "submission",
          description: "Percentage of the render resolution to use for playblast"},
        { key: "use_viewport_settings", type: "bool", default: true, visible: "submission",
          description: "Use current viewport display settings for playblast"},
        { key: "display_mode", type: "string", required: true, default: "SOLID", visible: "submission",
          description: "Viewport display mode (WIREFRAME, SOLID, MATERIAL, RENDERED)",
          choices: ["WIREFRAME", "SOLID", "MATERIAL", "RENDERED"] },

        // Automatically evaluated settings:
        { key: "blendfile", type: "string", required: true, description: "Path of the Blend file to playblast", visible: "web" },
        { key: "fps", type: "float", eval: "C.scene.render.fps / C.scene.render.fps_base", visible: "hidden" },
        { key: "format", type: "string", required: true, default: "PNG", visible: "web",
          description: "Image format for playblast frames" },
        { key: "image_file_extension", type: "string", required: true, default: ".png", visible: "hidden",
          description: "File extension used when creating playblast images" },
        { key: "scene", type: "string", required: true, eval: "C.scene.name", visible: "web",
          description: "Name of the scene to playblast."},
    ]
};

// File formats that would cause rendering to video.
// This is not supported by this job type.
const videoFormats = ['FFMPEG', 'AVI_RAW', 'AVI_JPEG'];

function compileJob(job) {
    print("BasedPlayblast job submitted");
    print("job: ", job);

    const settings = job.settings;
    if (videoFormats.indexOf(settings.format) >= 0) {
        throw `This job type only creates image sequences, and not "${settings.format}"`;
    }

    const playblastOutput = playblastOutputPath(job);

    // Make sure that when the job is investigated later, it shows the
    // actually-used playblast output:
    settings.playblast_output_path = playblastOutput;

    const playblastDir = path.dirname(playblastOutput);
    const playblastTasks = authorPlayblastTasks(settings, playblastDir, playblastOutput);
    const videoTask = authorCreateVideoTask(settings, playblastDir);

    for (const pt of playblastTasks) {
        job.addTask(pt);
    }
    if (videoTask) {
        // If there is a video task, all other tasks have to be done first.
        for (const pt of playblastTasks) {
            videoTask.addDependency(pt);
        }
        job.addTask(videoTask);
    }
}

// Do field replacement on the playblast output path.
function playblastOutputPath(job) {
    let path = job.settings.playblast_output_path;
    if (!path) {
        throw "no playblast_output_path setting!";
    }
    return path.replace(/{([^}]+)}/g, (match, group0) => {
        switch (group0) {
        case "timestamp":
            return formatTimestampLocal(job.created);
        default:
            return match;
        }
    });
}

function authorPlayblastTasks(settings, playblastDir, playblastOutput) {
    print("authorPlayblastTasks(", playblastDir, playblastOutput, ")");
    let playblastTasks = [];
    let chunks = frameChunker(settings.frames, settings.chunk_size);

    let baseArgs = [];
    if (settings.scene) {
      baseArgs = baseArgs.concat(["--scene", settings.scene]);
    }

    for (let chunk of chunks) {
        const task = author.Task(`playblast-${chunk}`, "blender");
        const command = author.Command("blender-render", {
            exe: "{blender}",
            exeArgs: "{blenderArgs}",
            argsBefore: [],
            blendfile: settings.blendfile,
            args: baseArgs.concat([
                "--python-expr", `
import bpy

# Set resolution percentage
bpy.context.scene.render.resolution_percentage = ${settings.resolution_percentage}

# Find a 3D view to use for playblast
area = None
for a in bpy.context.screen.areas:
    if a.type == 'VIEW_3D':
        area = a
        break

if area:
    # Store original settings
    space = area.spaces.active
    original_shading = space.shading.type
    original_overlays = space.overlay.show_overlays
    
    # Switch to desired display mode
    space.shading.type = '${settings.display_mode}'
    
    # Disable overlays for cleaner output
    space.overlay.show_overlays = False
    
    # Make sure we're in camera view
    region_3d = None
    for region in area.regions:
        if region.type == 'WINDOW':
            region_3d = space.region_3d
            break
    
    if region_3d:
        # Switch to camera view if needed
        original_perspective = region_3d.view_perspective
        region_3d.view_perspective = 'CAMERA'

# Now perform the OpenGL render (playblast)
bpy.ops.render.opengl(animation=True, 
                     render_keyed_only=False, 
                     sequencer=False, 
                     write_still=True, 
                     view_context=${settings.use_viewport_settings})

# Restore original settings if we found and modified a 3D view
if area:
    space.shading.type = original_shading
    space.overlay.show_overlays = original_overlays
    if region_3d and 'original_perspective' in locals():
        region_3d.view_perspective = original_perspective
`,
                "--render-output", path.join(playblastDir, path.basename(playblastOutput)),
                "--render-format", settings.format,
                "--render-frame", chunk.replaceAll("-", ".."), // Convert to Blender frame range notation.
            ])
        });
        task.addCommand(command);
        playblastTasks.push(task);
    }
    return playblastTasks;
}

function authorCreateVideoTask(settings, playblastDir) {
    if (!settings.fps) {
        print("Not authoring video task, no FPS known:", settings);
        return;
    }

    var frames = `${settings.frames}`;
    if (frames.search(',') != -1) {
        // Get the first and last frame from the list
        const chunks = frameChunker(settings.frames, 1);
        const firstFrame = chunks[0];
        const lastFrame = chunks.slice(-1)[0];
        frames = `${firstFrame}-${lastFrame}`;
    }

    const stem = path.stem(settings.blendfile).replace('.flamenco', '');
    const outfile = path.join(playblastDir, `${stem}-blast-${frames}.mp4`);

    const task = author.Task('playblast-video', 'ffmpeg');
    const command = author.Command("frames-to-video", {
        exe: "ffmpeg",
        fps: settings.fps,
        inputGlob: path.join(playblastDir, `*${settings.image_file_extension}`),
        outputFile: outfile,
        args: [
            '-c:v',
            'h264_nvenc',
            '-preset',
            'medium',
            '-rc',
            'constqp',
            '-qp',
            '20',
            '-g',
            '18',
            '-vf',
            'pad=ceil(iw/2)*2:ceil(ih/2)*2',
            '-pix_fmt',
            'yuv420p',
            '-r',
            settings.fps,
            '-y', // Be sure to always pass either "-n" or "-y".
        ],
    });
    task.addCommand(command);

    print(`Creating output video for playblast`);
    return task;
}
