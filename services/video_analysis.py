import os
import cv2 # Still needed for getting video duration/properties, not frame extraction
import base64
import google.generativeai as genai
from moviepy.editor import VideoFileClip # Still needed for audio properties
import json
import time
from flask import session # Import session if needed for context, but not for direct script storage
import shutil # For robust directory removal

# Configure Google Generative AI with the API key
def configure_gemini(api_key):
    genai.configure(api_key=api_key)

# This function is no longer needed for frame-by-frame analysis but kept for reference
def get_base64_encoded_image_for_gemini(image_path, mime_type="image/jpeg"):
    """Encodes an image file to a base64 string and returns in Gemini's inline_data format."""
    with open(image_path, "rb") as image_file:
        return {
            "mime_type": mime_type,
            "data": base64.b64encode(image_file.read()).decode("utf-8")
        }

def wait_for_file_active(file_object, timeout=300, interval=5):
    """
    Polls the Gemini File API to check if an uploaded file is in 'ACTIVE' state.

    Args:
        file_object (genai.types.File): The File object returned by genai.upload_file.
        timeout (int): Maximum time to wait in seconds.
        interval (int): How often to check file status in seconds.

    Raises:
        Exception: If the file does not become active within the timeout.
    """
    print(f"Waiting for file '{file_object.display_name}' to become ACTIVE...")
    start_time = time.time()
    while True:
        if (time.time() - start_time) > timeout:
            raise Exception(f"File '{file_object.display_name}' did not become ACTIVE within {timeout} seconds.")

        retrieved_file = genai.get_file(file_object.name)
        if retrieved_file.state.name == 'ACTIVE':
            print(f"File '{file_object.display_name}' is now ACTIVE.")
            return retrieved_file
        elif retrieved_file.state.name == 'FAILED':
            raise Exception(f"File '{retrieved_file.display_name}' processing FAILED.") # Use display_name here

        print(f"File state: {retrieved_file.state.name}. Waiting {interval} seconds...")
        time.sleep(interval)


def analyze_video_with_openai(video_path, temp_output_dir, gemini_api_key):
    """
    Analyzes an entire video by uploading it to Google's Gemini API,
    and then processing the generated script.

    Args:
        video_path (str): The file path to the input video.
        temp_output_dir (str): A temporary directory for any intermediate files (less used now).
        gemini_api_key (str): The Gemini API key to use for authentication.

    Yields:
        dict: Progress updates for the frontend (status, progress, message).
    Returns:
        list: The final synthesized script content.
    """

    if not gemini_api_key:
        raise ValueError("Gemini API Key is required for video analysis but was not provided.")

    configure_gemini(gemini_api_key)

    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    print(f"Starting direct video analysis with Gemini for: {video_path}")
    yield {"status": "in_progress", "progress": 5, "message": "Analysis: Initializing upload to Gemini..."}

    uploaded_file = None
    synthesized_script_content = [] # Initialize as empty list to ensure it's always a list

    try:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type or not mime_type.startswith('video/'):
            raise ValueError(f"Could not determine video MIME type or it's not a video: {mime_type}")

        yield {"status": "in_progress", "progress": 10, "message": "Analysis: Uploading video to Gemini File API..."}
        print(f"Uploading video to Gemini File API: {video_path} with MIME type {mime_type}")
        uploaded_file = genai.upload_file(path=video_path, display_name=os.path.basename(video_path), mime_type=mime_type)
        print(f"Uploaded file URI: {uploaded_file.uri}")
        yield {"status": "in_progress", "progress": 30, "message": "Analysis: File uploaded. Waiting for processing..."}

        active_uploaded_file = wait_for_file_active(uploaded_file)
        yield {"status": "in_progress", "progress": 60, "message": "Analysis: File ready. Sending to model..."}

        # UPDATED PROMPT for narrative description
        prompt_parts = [
            active_uploaded_file,
            "Analyze the attached video and provide a continuous, fluid narrative description of what is happening throughout the video. Focus on key actions, subjects, and the environment. Do not include explicit timestamps or bullet points. Describe the flow of events as if you are a narrator speaking about the video."
        ]

        print("Sending analysis request to Gemini...")
        response = gemini_model.generate_content(prompt_parts)
        synthesized_text = response.text
        print("Gemini analysis complete.")
        yield {"status": "in_progress", "progress": 90, "message": "Analysis: Model response received. Parsing script..."}

        # For narrative output, we'll store it as a single item in the list
        synthesized_script_content = [{"time": "Narrative", "description": synthesized_text.strip()}]

    except Exception as e:
        print(f"Error during Gemini video analysis: {e}")
        error_message = f"Video analysis failed: {str(e)}"
        # Ensure synthesized_script_content is still a list, even on error
        synthesized_script_content = [{"time": "Error", "description": error_message + " Please check your Gemini API key and try again."}]
        yield {"status": "error", "progress": 0, "message": error_message}
    finally: # Moved finally block to ensure cleanup
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
                print(f"Cleaned up uploaded file: {uploaded_file.name}")
            except Exception as e:
                print(f"Error cleaning up Gemini uploaded file {uploaded_file.name}: {e}")

        if os.path.exists(temp_output_dir): # Check if directory exists before trying to remove
            try:
                shutil.rmtree(temp_output_dir, ignore_errors=True) # Use rmtree for non-empty dirs
                print(f"Cleaned up temporary directory: {temp_output_dir}")
            except Exception as e:
                print(f"Error removing temporary directory {temp_output_dir}: {e}")

    # This function now RETURNS the script content, it does not yield it as a special dict.
    return synthesized_script_content
