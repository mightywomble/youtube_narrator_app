import subprocess
import os
import json # For progress message encoding

def merge_video_audio(video_input_path, audio_input_path, output_path):
    """
    Merges a video file with an audio file using FFmpeg.

    Args:
        video_input_path (str): Path to the input video file.
        audio_input_path (str): Path to the input audio file.
        output_path (str): Path where the merged video will be saved.

    Yields:
        str: JSON string indicating progress or completion for SSE.
    Returns:
        str: The path to the saved merged video file on success.
    """
    # FFmpeg command to merge video and audio
    command = [
        'ffmpeg',
        '-i', video_input_path,
        '-i', audio_input_path,
        '-c:v', 'copy', # Copy video stream
        '-c:a', 'aac',  # Re-encode audio to AAC for broader compatibility
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-y', # Overwrite output file if it exists
        output_path
    ]

    print(f"Starting video merge with FFmpeg: {video_input_path} + {audio_input_path} -> {output_path}")
    yield json.dumps({'status': 'in_progress', 'progress': 5, 'message': 'Merge: Initializing FFmpeg...'})

    try:
        # Use subprocess.Popen to run FFmpeg and capture its output for progress
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Get video duration for progress calculation (using ffprobe)
        total_duration = None
        try:
            duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_input_path]
            duration_output = subprocess.check_output(duration_cmd, text=True).strip()
            total_duration = float(duration_output)
            print(f"Video duration for merge progress: {total_duration:.2f} seconds")
        except Exception as e:
            print(f"Could not get video duration for progress: {e}. Proceeding without duration-based progress.")

        # Read FFmpeg's stderr line by line for progress
        for line in process.stderr:
            if "time=" in line:
                try:
                    time_str = line.split("time=")[1].split(" ")[0].strip()
                    h, m, s = map(float, time_str.split(':'))
                    current_time_seconds = h * 3600 + m * 60 + s

                    if total_duration and total_duration > 0:
                        progress_percentage = int((current_time_seconds / total_duration) * 100)
                        if progress_percentage > 100: progress_percentage = 100 # Cap at 100
                        yield json.dumps({'status': 'in_progress', 'progress': progress_percentage, 'message': f'Merge: {progress_percentage}% complete'})
                except Exception as e:
                    # print(f"Error parsing FFmpeg progress line: {line.strip()} - {e}")
                    yield json.dumps({'status': 'in_progress', 'message': 'Merge: Processing...'})
            elif "Error" in line or "fail" in line.lower():
                print(f"FFmpeg error: {line.strip()}")
                raise Exception(f"FFmpeg encountered an error: {line.strip()}")

        process.wait() # Wait for the process to complete

        if process.returncode != 0:
            error_output = process.stderr.read()
            raise Exception(f"FFmpeg process failed with exit code {process.returncode}: {error_output}")

        # Verify output file exists
        if not os.path.exists(output_path):
            raise Exception(f"FFmpeg completed but output file was not found at {output_path}")

        yield json.dumps({'status': 'in_progress', 'progress': 100, 'message': 'Merge: Complete. Finalizing...'})

    except FileNotFoundError:
        raise FileNotFoundError("FFmpeg not found. Please ensure FFmpeg is installed and in your system's PATH.")
    except Exception as e:
        print(f"Error during video merging: {e}")
        yield json.dumps({'status': 'error', 'message': f'Video merging failed: {str(e)}'})
        raise # Re-raise the exception for the caller to handle

    # Return the path on successful completion
    return output_path

