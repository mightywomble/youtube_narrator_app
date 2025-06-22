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
    """
    # FFmpeg command to merge video and audio
    # -i: input file
    # -c:v copy: copy video stream without re-encoding (faster, preserves quality)
    # -map 0:v:0: map first video stream from first input
    # -map 1:a:0: map first audio stream from second input
    # -y: overwrite output file without asking
    command = [
        'ffmpeg',
        '-i', video_input_path,
        '-i', audio_input_path,
        '-c:v', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-y', # Overwrite output file if it exists
        output_path
    ]

    try:
        # Use subprocess.Popen to run FFmpeg and capture its output for progress
        # stderr is captured to parse progress as FFmpeg usually prints to stderr
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Get video duration for progress calculation (using ffprobe)
        try:
            duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_input_path]
            duration_output = subprocess.check_output(duration_cmd, text=True).strip()
            total_duration = float(duration_output)
        except Exception as e:
            print(f"Could not get video duration for progress: {e}. Proceeding without duration-based progress.")
            total_duration = None # Fallback if ffprobe fails

        # Read FFmpeg's stderr line by line for progress
        for line in process.stderr:
            if "time=" in line:
                try:
                    time_str = line.split("time=")[1].split(" ")[0].strip()
                    h, m, s = map(float, time_str.split(':'))
                    current_time_seconds = h * 3600 + m * 60 + s
                    
                    if total_duration:
                        progress_percentage = int((current_time_seconds / total_duration) * 100)
                        if progress_percentage > 100: progress_percentage = 100 # Cap at 100
                        yield json.dumps({'status': 'in_progress', 'progress': progress_percentage, 'message': f'Merging video: {progress_percentage}% complete'})
                except Exception as e:
                    # print(f"Error parsing FFmpeg progress line: {line.strip()} - {e}")
                    yield json.dumps({'status': 'in_progress', 'message': 'Merging video...'})
            elif "Error" in line or "fail" in line.lower():
                print(f"FFmpeg error: {line.strip()}")
                raise Exception(f"FFmpeg encountered an error: {line.strip()}")

        process.wait() # Wait for the process to complete

        if process.returncode != 0:
            error_output = process.stderr.read()
            raise Exception(f"FFmpeg process failed with exit code {process.returncode}: {error_output}")

    except FileNotFoundError:
        raise FileNotFoundError("FFmpeg not found. Please ensure FFmpeg is installed and in your system's PATH.")
    except Exception as e:
        print(f"Error during video merging: {e}")
        raise

    yield json.dumps({'status': 'complete', 'message': 'Video merge complete!'})

