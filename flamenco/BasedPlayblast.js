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
        { key: "playblast_output_root", type: "string", subtype: "dir_path", required: true, default: "//", visible: "submission",
          description: "Base directory of where playblast output is stored. Will have some job-specific parts appended to it"},
        { key: "add_path_components", type: "int32", required: true, default: 0, propargs: {min: 0, max: 32}, visible: "submission",
          description: "Number of path components of the current blend file to use in the playblast output path"},
        { key: "playblast_output_path", type: "string", subtype: "file_path", editable: false,
          eval: "str(Path(abspath(settings.playblast_output_root), last_n_dir_parts(settings.add_path_components), 'blast', jobname, jobname + '_######'))",
          description: "Final file path of where playblast output will be saved"},
          
        // Playblast specific settings
        { key: "resolution_percentage", type: "int32", default: 100, propargs: {min: 1, max: 100}, visible: "submission",
          description: "Percentage of the render resolution to use for playblast"},
        { key: "keep_frames", type: "bool", default: false, visible: "submission",
          description: "Keep the individual playblast frames after video creation"},

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

    // Get the blast base directory (without jobname subfolder)
    const baseDir = path.dirname(path.dirname(playblastOutput));
    const playblastDir = path.dirname(playblastOutput);
    
    const playblastTasks = authorPlayblastTasks(settings, playblastDir, playblastOutput);
    const tasks = authorCreateVideoTask(settings, playblastDir, baseDir);
    
    // Add all playblast tasks
    for (const pt of playblastTasks) {
        job.addTask(pt);
    }
    
    // Add video task and make it dependent on playblast tasks
    if (tasks && tasks.length > 0) {
        const videoTask = tasks[0];
        // Video task depends on all playblast tasks
        for (const pt of playblastTasks) {
            videoTask.addDependency(pt);
        }
        job.addTask(videoTask);
        
        // If there's a cleanup task, add it too
        if (tasks.length > 1) {
            const cleanupTask = tasks[1];
            job.addTask(cleanupTask);
        }
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
        
        // Use standard rendering with the blend file's existing settings
        const renderCommand = author.Command("blender-render", {
            exe: "{blender}",
            exeArgs: "{blenderArgs}",
            argsBefore: [],
            blendfile: settings.blendfile,
            args: baseArgs.concat([
                "--python-expr", `
import bpy

# Just render the specified frames via --render-frame
# Skip using animation=True which would render all frames
`,
                "--render-output", path.join(playblastDir, path.basename(playblastOutput)),
                "--render-format", settings.format,
                "--render-frame", chunk.replaceAll("-", "..")
            ])
        });
        
        task.addCommand(renderCommand);
        playblastTasks.push(task);
    }
    return playblastTasks;
}

function authorCreateVideoTask(settings, playblastDir, baseDir) {
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

    const jobname = path.stem(path.basename(playblastDir));
    // Create video output path directly in the blast folder with the naming convention blast_[jobname]_[frames].mp4
    const outfile = path.join(baseDir, `blast_${jobname}_${frames}.mp4`);
    const inputGlob = path.join(playblastDir, `*${settings.image_file_extension}`);

    // Create the ffmpeg task
    const videoTask = author.Task('playblast-video', 'ffmpeg');
    
    // Command to create the video from frames
    const ffmpegCommand = author.Command("frames-to-video", {
        exe: "ffmpeg",
        fps: settings.fps,
        inputGlob: inputGlob,
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
    
    videoTask.addCommand(ffmpegCommand);
    
    // Only create cleanup task if keep_frames is false
    if (!settings.keep_frames) {
        // Create a separate Blender task for cleanup
        const cleanupTask = author.Task('playblast-cleanup', 'blender');
        
        // Command to delete the frame images and job folder after video creation using Blender Python
        const cleanupCommand = author.Command("blender-render", {
            exe: "{blender}",
            exeArgs: "{blenderArgs}",
            blendfile: "",  // Empty to avoid loading a blend file
            argsBefore: ["-b", "--python-expr"],
            args: [`
import os
import glob
import sys
import shutil
import time

# Get the path to clean up
cleanup_pattern = "${inputGlob.replace(/\\/g, '\\\\')}"
job_folder = "${playblastDir.replace(/\\/g, '\\\\')}"
print(f"Cleaning up temporary frames: {cleanup_pattern}")

# Find all matching files
files = glob.glob(cleanup_pattern)
print(f"Found {len(files)} files to delete")

# Delete each file
deleted_count = 0
for file in files:
    try:
        os.remove(file)
        deleted_count += 1
    except Exception as e:
        print(f"Error deleting {file}: {e}")

print(f"Cleanup completed: {deleted_count} files deleted")

# Small delay to ensure file operations are complete
time.sleep(0.5)

# Now forcibly delete the job folder since we know we've removed all important files
try:
    if os.path.exists(job_folder):
        # List contents for debugging
        remaining_files = os.listdir(job_folder)
        if remaining_files:
            print(f"Detected remaining files in job folder: {remaining_files}")
            print("These are likely system files or metadata which can be safely removed")
        
        # Force deletion regardless of content
        shutil.rmtree(job_folder)
        print(f"Deleted job folder: {job_folder}")
    else:
        print(f"Job folder does not exist: {job_folder}")
except Exception as e:
    print(f"Error deleting job folder: {e}")

sys.exit(0)  # Exit with success code regardless of folder deletion
`]
        });
        
        cleanupTask.addCommand(cleanupCommand);
        
        // Make the cleanup task dependent on the video task
        cleanupTask.addDependency(videoTask);
        
        print(`Creating output video for playblast and cleanup task for temporary frames`);
        
        // Return both tasks
        return [videoTask, cleanupTask];
    } else {
        print(`Creating output video for playblast (keeping frames as requested)`);
        
        // Return only the video task
        return [videoTask];
    }
}
