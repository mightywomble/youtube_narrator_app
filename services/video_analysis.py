import os
import cv2 # Still needed for getting video duration/properties, not frame extraction
import base64
import google.generativeai as genai
from moviepy.editor import VideoFileClip # Still needed for audio properties
import json
import time

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
            raise Exception(f"File '{file_object.display_name}' processing FAILED.")

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

    Returns:
        list: A list of dictionaries, each containing 'time' and 'description' for the synthesized script.
    """

    if not gemini_api_key:
        raise ValueError("Gemini API Key is required for video analysis but was not provided.")

    configure_gemini(gemini_api_key)

    # Use gemini-1.5-flash for video understanding
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    print(f"Starting direct video analysis with Gemini for: {video_path}")

    uploaded_file = None # Initialize to None for the finally block
    try:
        # Get MIME type for the video file
        import mimetypes
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type or not mime_type.startswith('video/'):
            raise ValueError(f"Could not determine video MIME type or it's not a video: {mime_type}")

        # Upload the video file using Gemini's File API
        print(f"Uploading video to Gemini File API: {video_path} with MIME type {mime_type}")
        uploaded_file = genai.upload_file(path=video_path, display_name=os.path.basename(video_path), mime_type=mime_type)
        print(f"Uploaded file URI: {uploaded_file.uri}")

        # Wait for the uploaded file to become ACTIVE
        active_uploaded_file = wait_for_file_active(uploaded_file)

        # Construct the prompt with the file part (using the ACTIVE file)
        prompt_parts = [
            active_uploaded_file, # Use the file object that is confirmed ACTIVE
            "Analyse the attached video and create a script based on the timings in the video explaining what is happening in the video. Format the output as a list of timestamped descriptions. Example: '00:05 - A person enters the room. 00:10 - They sit at a desk.' Ensure all significant events throughout the entire video are captured with accurate timestamps."
        ]

        print("Sending analysis request to Gemini...")
        response = gemini_model.generate_content(prompt_parts)
        synthesized_text = response.text
        print("Gemini analysis complete.")

        # --- Post-processing: Parse the Gemini response into structured script_data ---
        synthesized_script_content = []

        # Heuristic to parse Gemini's response (assumes "MM:SS - Description" format)
        for line in synthesized_text.split('\n'):
            line = line.strip()
            # Basic check for timestamp format MM:SS -
            if line and len(line) > 5 and line[2] == ':' and line[5] == ' ':
                parts = line.split(' - ', 1) # Split only on the first ' - '
                if len(parts) == 2:
                    synthesized_script_content.append({
                        "time": parts[0].strip(),
                        "description": parts[1].strip()
                    })
                else: # Fallback if parsing fails, but line exists
                     synthesized_script_content.append({
                        "time": "",
                        "description": line
                    })
            elif line: # Add non-timestamped lines as descriptions
                 synthesized_script_content.append({
                    "time": "",
                    "description": line
                })

    except Exception as e:
        print(f"Error during Gemini video analysis: {e}")
        synthesized_script_content = [{"time": "00:00", "description": f"Video analysis failed: {str(e)} Please check your Gemini API key and try again."}]
    finally:
        # IMPORTANT: Clean up the uploaded file from Gemini's File API
        # This prevents incurring storage costs and adheres to good practice.
        if uploaded_file: # Ensure uploaded_file exists
            try:
                genai.delete_file(uploaded_file.name)
                print(f"Cleaned up uploaded file: {uploaded_file.name}")
            except Exception as e:
                print(f"Error cleaning up Gemini uploaded file {uploaded_file.name}: {e}")

        # Clean up local temporary directory (from previous frame extraction, now mostly empty)
        try:
            os.rmdir(temp_output_dir)
        except OSError as e:
            if "Directory not empty" in str(e):
                # This can happen if previous runs left files, or if there's a delay in OS cleanup
                print(f"Warning: Could not remove temporary directory {temp_output_dir}: {e}. It might not be empty from prior runs.")
            else:
                print(f"Error removing temporary directory {temp_output_dir}: {e}")

    return synthesized_script_content

