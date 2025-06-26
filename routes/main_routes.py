import os
import uuid
from flask import Blueprint, request, jsonify, render_template, current_app, session, Response
from werkzeug.utils import secure_filename
import time
import json # For JSON encoding of SSE messages

# Import services
from services.video_analysis import analyze_video_with_openai
from services.audio_synthesis import convert_text_to_speech_gemini
from services.video_merging import merge_video_audio
from services.youtube_api import upload_video_to_youtube # Placeholder for now

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Renders the main application page."""
    # Clear session data on fresh load to prevent stale information
    if 'video_path' in session:
        session.pop('video_path', None)
    if 'script' in session:
        session.pop('script', None)
    if 'audio_path' in session:
        session.pop('audio_path', None)
    if 'merged_video_path' in session:
        session.pop('merged_video_path', None)
    return render_template('index.html')

@main_bp.route('/upload_video', methods=['POST'])
def upload_video():
    """
    Handles video file upload and initiates analysis.
    Returns JSON response for initial upload status.
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected video file'}), 400

    if file:
        # Create a unique filename for the uploaded video
        unique_filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

        # Store original video path in session immediately for later use
        session['video_path'] = video_path

        # Save the file to disk here
        try:
            print(f"Saving uploaded file to: {video_path}")
            file.save(video_path)
            print("File saved successfully.")
        except Exception as e:
            current_app.logger.error(f"Error saving uploaded file: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to save uploaded file: {str(e)}'}), 500

        # Now, return a JSON response indicating successful upload,
        # which will trigger the frontend to open a new SSE connection for analysis.
        return jsonify({
            'status': 'success',
            'message': 'Video uploaded. Starting analysis...',
            'unique_filename': unique_filename,
            'video_url': f'/static/uploads/{unique_filename}'
        })

    return jsonify({'error': 'An unexpected error occurred during upload.'}), 500

@main_bp.route('/stream_analysis_progress')
def stream_analysis_progress():
    """
    Streams progress updates for video analysis using Server-Sent Events (SSE).
    This route is called *after* the initial file upload is complete.
    """
    unique_filename = request.args.get('video_filename')
    if not unique_filename:
        return Response(f"data: {json.dumps({'status': 'error', 'message': 'Missing video_filename parameter.'})}\n\n", mimetype='text/event-stream')

    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    if not os.path.exists(video_path):
        return Response(f"data: {json.dumps({'status': 'error', 'message': 'Video file not found for analysis.'})}\n\n", mimetype='text/event-stream')

    # Get the application instance to push context (if needed for things other than current_app.logger)
    app = current_app._get_current_object() # Get the real app object from the proxy

    final_script_for_session = [] # To capture the script returned by the analysis generator

    # Define the generator function here, right before it's used
    def generate_analysis_stream():
        nonlocal final_script_for_session # To modify this variable

        # Create a temporary request context for the duration of the generator
        with app.test_request_context():
            try:
                temp_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_analysis_' + str(uuid.uuid4()))
                os.makedirs(temp_output_dir, exist_ok=True)

                gemini_key = current_app.config.get('GEMINI_API_KEY')
                if not gemini_key:
                    raise ValueError("Gemini API Key is not configured. Please set it in settings.")

                yield f"data: {json.dumps({'status': 'in_progress', 'progress': 0, 'message': 'Analysis: Initializing Gemini analysis...'})}\n\n"

                analysis_generator_obj = analyze_video_with_openai(video_path, temp_output_dir, gemini_key)

                script_data_returned = None # Initialize to None to differentiate from empty list
                while True: # Loop through the generator to get progress and capture return value
                    try:
                        progress_update = next(analysis_generator_obj)
                        # The analyze_video_with_openai service now RETURNS the script, it does not yield it.
                        # So, this 'if isinstance(progress_update, dict) and 'final_script_data' in progress_update:'
                        # block should theoretically not be hit for the final script.
                        # It will only yield progress updates.
                        yield f"data: {json.dumps(progress_update)}\n\n" # Yield regular progress updates
                    except StopIteration as e:
                        script_data_returned = e.value # Capture the return value of the generator
                        break # Exit loop

                # --- Debugging Log ---
                current_app.logger.debug(f"Analysis Generator returned: {script_data_returned}, type: {type(script_data_returned)}")
                # --- End Debugging Log ---

                # Ensure script_data_returned is a list, even if analysis returned None or unexpected
                if not isinstance(script_data_returned, list):
                    current_app.logger.warning(f"analyze_video_with_openai did not return a list for script data. Received type: {type(script_data_returned)}, value: {script_data_returned}")
                    script_data_returned = [] # Default to empty list to prevent frontend .map() error

                final_script_for_session = script_data_returned # Store in nonlocal variable
                session['script'] = final_script_for_session # Store in session here

                yield f"data: {json.dumps({'status': 'complete', 'message': 'Analysis: Complete!', 'script': final_script_for_session})}\n\n"

            except Exception as e:
                error_message = f"Video analysis failed: {str(e)}"
                if os.path.exists(video_path):
                    os.remove(video_path)
                current_app.logger.error(error_message, exc_info=True)
                yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
            finally:
                # Cleanup of temp_output_dir is handled in video_analysis.py's finally block now.
                pass # No need for cleanup here, it's in the service.

    return Response(generate_analysis_stream(), mimetype='text/event-stream')


@main_bp.route('/generate_speech', methods=['POST'])
def generate_speech():
    """
    Converts the provided script text to speech.
    This route will now execute the TTS generation fully and then return a JSON response
    with the final status and audio URL.
    Progress updates will be less granular (only start/complete from Flask's perspective).
    """
    script_text = request.json.get('script_text')
    if not script_text:
        return jsonify({'error': 'No script text provided'}), 400

    video_path = session.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Original video not found. Please upload again.'}), 400

    # Get the application instance to push context (required for session access and current_app.config)
    app = current_app._get_current_object()

    # Generate a unique filename for the audio
    audio_filename = str(uuid.uuid4()) + ".mp3"
    audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)

    with app.app_context(): # Ensure application context for current_app.config and session access
        try:
            print("Starting speech generation (server-side, blocking process)...")

            # Execute the convert_text_to_speech_gemini generator fully to get the final audio path
            tts_generator = convert_text_to_speech_gemini(script_text, audio_path)

            final_audio_path_data = None
            # Iterate through the generator to execute it and capture its return value
            while True:
                try:
                    # Next call will execute up to the next yield or the return
                    progress_info = next(tts_generator)
                    # For this blocking route, we don't stream intermediate progress to frontend,
                    # but we can log them if needed.
                    current_app.logger.debug(f"TTS Service Progress (Internal): {json.loads(progress_info.strip('data: ')).get('message')}")
                except StopIteration as e:
                    final_audio_path_data = e.value # Capture the return value (the final audio path)
                    break # Exit loop

            # After the generator completes and returns, store the audio path in session
            session['audio_path'] = final_audio_path_data

            # Return the final JSON response
            return jsonify({
                'status': 'complete',
                'message': 'Speech generation complete!',
                'audio_url': f'/static/uploads/{os.path.basename(final_audio_path_data)}'
            })

        except Exception as e:
            current_app.logger.error(f"Speech generation failed: {str(e)}", exc_info=True)
            return jsonify({'error': f'Speech generation failed: {str(e)}'}), 500


@main_bp.route('/merge_video_audio', methods=['GET']) # Changed method to GET
def merge_video_audio_route():
    """Merges the uploaded video and generated audio."""
    video_path = session.get('video_path')
    audio_path = session.get('audio_path')

    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Original video not found. Please upload again.'}), 400
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'error': 'Generated audio not found. Please generate speech first.'}), 400

    merged_filename = str(uuid.uuid4()) + "_merged.mp4"
    merged_video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], merged_filename)

    app = current_app._get_current_object() # Get the real app object for context

    def progress_generator():
        # Push request context for session access within the generator
        with app.test_request_context():
            try:
                yield "data: {'status': 'in_progress', 'message': 'Starting video-audio merge...'}\n\n"

                # Execute the merge_video_audio service. It yields progress and returns the final path.
                merge_generator_obj = merge_video_audio(video_path, audio_path, merged_video_path)

                final_merged_video_path = None
                while True: # Loop through the generator to get progress and capture return value
                    try:
                        progress_info = next(merge_generator_obj)
                        yield f"data: {json.dumps(progress_info)}\n\n" # Yield progress updates
                    except StopIteration as e:
                        final_merged_video_path = e.value # Capture the return value (the final merged video path)
                        break # Exit loop

                session['merged_video_path'] = final_merged_video_path # Store merged video path in session
                yield f"data: {json.dumps({'status': 'complete', 'message': 'Merge complete!', 'merged_video_url': f'/static/uploads/{os.path.basename(final_merged_video_path)}'})}\n\n"

            except Exception as e:
                current_app.logger.error(f"Video merging failed within generator: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'status': 'error', 'message': f'Video merging failed: {str(e)}'})}\n\n"

    return Response(progress_generator(), mimetype='text/event-stream')


@main_bp.route('/upload_to_youtube', methods=['POST'])
def upload_to_youtube_route():
    """Initiates the YouTube video upload."""
    # These are retrieved from the session outside the generator, which is fine
    merged_video_path = session.get('merged_video_path')
    video_title = request.json.get('video_title', 'My AI Generated Video')
    video_description = request.json.get('video_description', 'A video generated with AI narration.')

    if not merged_video_path or not os.path.exists(merged_video_path):
        return jsonify({'error': 'Merged video not found. Please merge first.'}), 400

    app = current_app._get_current_object() # Get the real app object for context

    try:
        def youtube_upload_progress():
            with app.test_request_context(): # Push request context for session access if needed in the future
                try:
                    yield "data: {'status': 'in_progress', 'message': 'Starting YouTube upload...'}\n\n"
                    # This function will yield progress messages
                    for progress_info in upload_video_to_youtube(merged_video_path, video_title, video_description):
                        yield f"data: {progress_info}\n\n"
                    yield "data: {'status': 'complete', 'message': 'Upload to YouTube complete!'}\n\n"
                except Exception as e:
                    current_app.logger.error(f"YouTube upload failed within generator: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'status': 'error', 'message': f'YouTube upload failed: {str(e)}'})}\n\n"

        return Response(youtube_upload_progress(), mimetype='text/event-stream')

    except Exception as e:
        # This catch is for errors BEFORE the generator starts yielding
        current_app.logger.error(f"YouTube upload failed before generator: {str(e)}", exc_info=True)
        return jsonify({'error': f'YouTube upload failed: {str(e)}'}), 500

@main_bp.route('/cleanup_files', methods=['POST'])
def cleanup_files():
    """Cleans up temporary files in the uploads folder related to the session."""
    files_to_clean = [
        session.pop('video_path', None),
        session.pop('audio_path', None),
        session.pop('merged_video_path', None)
    ]
    # Remove script from session too
    session.pop('script', None)

    removed_count = 0
    for f_path in files_to_clean:
        if f_path and os.path.exists(f_path):
            try:
                os.remove(f_path)
            except Exception as e:
                current_app.logger.error(f"Error cleaning up file {f_path}: {e}", exc_info=True)

    return jsonify({'message': f'Cleaned up {removed_count} temporary files.'})
