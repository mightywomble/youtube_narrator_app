import os
import cv2
import base64
from openai import OpenAI
from moviepy.editor import VideoFileClip
import json # For progress message encoding
import time # For simulation of work

def get_base64_encoded_image(image_path):
    """Encodes an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_video_with_openai(video_path, temp_output_dir, openai_api_key):
    """
    Analyzes a video by extracting frames, sending them to OpenAI's GPT-4o Vision API,
    and generating a script. Optionally transcribes audio with Whisper.
    
    Args:
        video_path (str): The file path to the input video.
        temp_output_dir (str): A temporary directory to store extracted frames and audio.
        openai_api_key (str): The OpenAI API key to use for authentication.

    Returns:
        list: A list of dictionaries, each containing 'time' and 'description' for the script.
    """
    
    if not openai_api_key:
        raise ValueError("OpenAI API Key is required for video analysis but was not provided.")
    
    # Initialize OpenAI client. Removed 'proxies={}' as it caused a TypeError with this library version.
    # The client should pick up proxy settings from environment variables (HTTP_PROXY, HTTPS_PROXY)
    # if they are set on your system.
    client = OpenAI(api_key=openai_api_key)

    script_data = []
    
    # --- 1. Extract frames for Vision API analysis ---
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Determine frame interval: e.g., 1 frame every 2 seconds for a balance of detail and cost
    frame_sample_rate = 2 # seconds
    frame_interval = int(fps * frame_sample_rate)
    if frame_interval == 0: # Ensure at least one frame is processed if FPS is very low
        frame_interval = 1

    frame_count = 0
    print(f"Starting frame extraction and analysis for {video_path}...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break # End of video
        
        if frame_count % frame_interval == 0:
            frame_time_seconds = frame_count / fps
            # Generate a unique path for each frame to avoid conflicts
            frame_filename = os.path.join(temp_output_dir, f"frame_{int(frame_time_seconds):04d}_{os.urandom(4).hex()}.jpg")
            
            # Save frame temporarily
            cv2.imwrite(frame_filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 80]) # Save as JPEG with quality
            
            # --- 2. Analyze frame with GPT-4o Vision API ---
            base64_image = get_base64_encoded_image(frame_filename)
            
            try:
                # print(f"Analyzing frame at {frame_time_seconds:.2f}s...")
                response = client.chat.completions.create(
                    model="gpt-4o", # Using GPT-4o for its vision capabilities
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe what is happening in this video frame concisely, focusing on key actions, objects, and the environment. Keep it to one or two sentences. This will be part of a YouTube video script."},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}",
                                        "detail": "low" # 'low' for faster/cheaper, 'high' for more detail
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=150, # Limit the response length to keep descriptions concise
                )
                description = response.choices[0].message.content
                script_data.append({
                    "time": f"{int(frame_time_seconds // 60):02d}:{int(frame_time_seconds % 60):02d}",
                    "description": description.strip()
                })
            except Exception as e:
                print(f"Error analyzing frame {frame_filename} at {frame_time_seconds:.2f}s: {e}")
                script_data.append({
                    "time": f"{int(frame_time_seconds // 60):02d}:{int(frame_time_seconds % 60):02d}",
                    "description": f"Visual analysis failed for this moment. ({str(e)})"
                })
            finally:
                # Clean up frame image after use
                if os.path.exists(frame_filename):
                    os.remove(frame_filename)
            
        frame_count += 1
    
    cap.release()
    print("Frame analysis complete.")

    # --- 3. (Optional but Recommended) Audio Transcription with Whisper ---
    # This part requires pydub (pip install pydub) for audio conversion 
    # and ffmpeg/avconv installed on the system.
    audio_temp_path = os.path.join(temp_output_dir, "audio_track.mp3")
    transcript_text = ""
    try:
        print("Extracting audio for transcription...")
        video_clip = VideoFileClip(video_path)
        video_clip.audio.write_audiofile(audio_temp_path, codec='mp3')
        
        print("Transcribing audio with OpenAI Whisper...")
        with open(audio_temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        transcript_text = transcript.text
        print(f"Audio Transcription complete. Length: {len(transcript_text)} characters.")
        
    except Exception as e:
        print(f"Could not extract or transcribe audio with Whisper: {e}. Proceeding without audio transcript.")
    finally:
        if os.path.exists(audio_temp_path):
            os.remove(audio_temp_path)
    
    # --- 4. Refine Script (Optional, but makes script more coherent) ---
    # Combine visual descriptions and audio transcript into a more coherent narrative.
    # This could involve another call to a text-based OpenAI model (e.g., GPT-4o text)
    # to synthesize the information.
    
    # For now, let's append the full transcript if available, or just return raw script_data
    final_script = []
    if transcript_text:
        final_script.append({"time": "00:00", "description": "Overall Audio Transcript: " + transcript_text[:500] + ("..." if len(transcript_text) > 500 else "")}) # Truncate for display
        final_script.extend(script_data) # Add visual descriptions after transcript summary
    else:
        final_script = script_data
        
    # Attempt to clean up the temporary directory. Requires it to be empty.
    # If not empty (e.g., if debugging and frames were left), rmdir will fail.
    try:
        os.rmdir(temp_output_dir)
    except OSError as e:
        print(f"Could not remove temporary directory {temp_output_dir}: {e}. It might not be empty.")

    return final_script

