import os
import cv2
import base64
import google.generativeai as genai # For Gemini
from moviepy.editor import VideoFileClip
import json
import time

# Configure Google Generative AI with the API key
def configure_gemini(api_key):
    genai.configure(api_key=api_key)

def get_base64_encoded_image_for_gemini(image_path, mime_type="image/jpeg"):
    """Encodes an image file to a base64 string and returns in Gemini's inline_data format."""
    with open(image_path, "rb") as image_file:
        return {
            "mime_type": mime_type,
            "data": base64.b64encode(image_file.read()).decode("utf-8")
        }

def analyze_video_with_openai(video_path, temp_output_dir, gemini_api_key):
    """
    Analyzes a video by extracting frames, sending them to Google's Gemini Pro Vision API,
    and generating a script. (OpenAI Whisper audio transcription is removed in this version).

    Args:
        video_path (str): The file path to the input video.
        temp_output_dir (str): A temporary directory to store extracted frames and audio.
        gemini_api_key (str): The Gemini API key to use for authentication.

    Returns:
        list: A list of dictionaries, each containing 'time' and 'description' for the script.
    """

    if not gemini_api_key:
        raise ValueError("Gemini API Key is required for video analysis but was not provided.")

    # Configure Gemini API
    configure_gemini(gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-pro-vision')

    script_data = []

    # --- 1. Extract frames for Vision API analysis ---
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration_seconds = total_frames / fps if fps > 0 else 0

    print(f"Video opened: {video_path}")
    print(f"FPS: {fps}")
    print(f"Total Frames: {total_frames}")
    print(f"Total Duration: {total_duration_seconds:.2f} seconds")

    # Determine frame interval: Analyzing 2 frames per second (0.5 seconds per frame)
    frame_sample_rate = 0.5 # seconds
    frame_interval = int(fps * frame_sample_rate)
    if frame_interval == 0:
        frame_interval = 1

    frame_count = 0
    print(f"Starting frame extraction and analysis with interval: every {frame_sample_rate}s (every {frame_interval} frames)...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"End of video or error reading frame. Processed {frame_count} frames.")
            break

        if frame_count % frame_interval == 0:
            frame_time_seconds = frame_count / fps
            frame_filename = os.path.join(temp_output_dir, f"frame_{int(frame_time_seconds):04d}_{os.urandom(4).hex()}.jpg")

            cv2.imwrite(frame_filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

            # --- 2. Analyze frame with Gemini Pro Vision API ---
            image_part = get_base64_encoded_image_for_gemini(frame_filename)

            try:
                print(f"Analyzing frame at {frame_time_seconds:.2f}s (Frame {frame_count})...")
                # Constructing the prompt as a list for multimodal input
                gemini_prompt_parts = [
                    image_part,
                    "This image is a frame from a video. Your task is to analyze the entire video and create a script based on its content, matching timestamps. For this specific frame, describe concisely what is happening, focusing on key actions, objects, and the environment. Keep your description to 1-2 sentences, suitable as a line in a sequential video script."
                ]

                response = gemini_model.generate_content(gemini_prompt_parts)
                description = response.text
                script_data.append({
                    "time": f"{int(frame_time_seconds // 60):02d}:{int(frame_time_seconds % 60):02d}",
                    "description": description.strip()
                })
            except Exception as e:
                print(f"Error analyzing frame {frame_filename} at {frame_time_seconds:.2f}s with Gemini: {e}")
                script_data.append({
                    "time": f"{int(frame_time_seconds // 60):02d}:{int(frame_time_seconds % 60):02d}",
                    "description": f"Visual analysis failed for this moment. ({str(e)})"
                })
            finally:
                if os.path.exists(frame_filename):
                    os.remove(frame_filename)

        frame_count += 1

    cap.release()
    print("Frame extraction and analysis complete.")

    # --- 3. Removed: Audio Transcription with Whisper (OpenAI) ---
    # This functionality is temporarily removed to isolate the 'proxies' issue.
    # It can be re-added later if needed, potentially as a separate service.
    transcript_text = "" # No audio transcript in this version

    # --- 4. Refine Script ---
    # Since no audio transcript, just return the visual script data
    final_script = script_data

    try:
        os.rmdir(temp_output_dir)
    except OSError as e:
        print(f"Could not remove temporary directory {temp_output_dir}: {e}. It might not be empty.")

    return final_script
