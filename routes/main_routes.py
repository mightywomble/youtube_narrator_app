import os
import uuid
from flask import Blueprint, request, jsonify, render_template, current_app, session, Response
from werkzeug.utils import secure_filename
import time

# Import services
from services.video_analysis import analyze_video_with_openai
from services.audio_synthesis import convert_text_to_speech_gemini
from services.video_merging import merge_video_audio
from services.youtube_api import upload_video_to_youtube # Placeholder for now
from utils.helpers import generate_progress_stream

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
    """Handles video file upload and initiates analysis."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file part'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected video file'}), 400

    if file:
        # Create a unique filename to prevent clashes
        unique_filename = str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(video_path)
        
        session['video_path'] = video_path # Store path in session
        
        try:
            # Create a temporary output directory for frames/audio
            temp_output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_analysis_' + str(uuid.uuid4()))
            os.makedirs(temp_output_dir, exist_ok=True)
            
            # Pass the OpenAI API key explicitly from the current_app config
            openai_key = current_app.config.get('OPENAI_API_KEY')
            if not openai_key:
                raise ValueError("OpenAI API Key is not configured. Please set it in settings.")

            # Analyze video and get script data
            script = analyze_video_with_openai(video_path, temp_output_dir, openai_key)
            session['script'] = script # Store script in session
            
            # Clean up temp_output_dir (optional, or keep for debugging)
            # os.rmdir(temp_output_dir) # This would delete empty dir, need to delete contents first
            
            return jsonify({'message': 'Video uploaded and analysis initiated!', 'script': script, 'video_url': f'/static/uploads/{unique_filename}'})
        except Exception as e:
            # Clean up uploaded video if analysis fails
            if os.path.exists(video_path):
                os.remove(video_path)
            # Log the full traceback for debugging
            current_app.logger.error(f"Video analysis failed: {str(e)}", exc_info=True)
            return jsonify({'error': f'Video analysis failed: {str(e)}'}), 500
    
    return jsonify({'error': 'An unexpected error occurred during upload.'}), 500

@main_bp.route('/generate_speech', methods=['POST'])
def generate_speech():
    """Converts the provided script text to speech."""
    script_text = request.json.get('script_text')
    if not script_text:
        return jsonify({'error': 'No script text provided'}), 400

    video_path = session.get('video_path')
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Original video not found. Please upload again.'}), 400

    # Generate a unique filename for the audio
    audio_filename = str(uuid.uuid4()) + ".mp3"
    audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)

    try:
        def generate():
            yield "data: {'status': 'in_progress', 'message': 'Starting speech generation...'}\n\n"
            
            # This is where the Gemini API call would happen from the backend.
            # For this example, we will make a dummy call to the service.
            # The prompt in audio_synthesis.py will ensure the Gemini call works.
            for progress_info in convert_text_to_speech_gemini(script_text, audio_path):
                yield f"data: {progress_info}\n\n"
            
            session['audio_path'] = audio_path # Store audio path in session
            yield "data: {'status': 'complete', 'message': 'Speech generation complete!', 'audio_url': '" + f'/static/uploads/{audio_filename}' + "'}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        current_app.logger.error(f"Speech generation failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Speech generation failed: {str(e)}'}), 500

@main_bp.route('/merge_video_audio', methods=['POST'])
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

    try:
        # Use a generator to stream progress updates
        def progress_generator():
            yield "data: {'status': 'in_progress', 'message': 'Starting video-audio merge...'}\n\n"
            for progress_info in merge_video_audio(video_path, audio_path, merged_video_path):
                yield f"data: {progress_info}\n\n"
            
            session['merged_video_path'] = merged_video_path # Store merged video path
            yield "data: {'status': 'complete', 'message': 'Merge complete!', 'merged_video_url': '" + f'/static/uploads/{merged_filename}' + "'}\n\n"
        
        return Response(progress_generator(), mimetype='text/event-stream')

    except Exception as e:
        current_app.logger.error(f"Video merging failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Video merging failed: {str(e)}'}), 500


@main_bp.route('/upload_to_youtube', methods=['POST'])
def upload_to_youtube_route():
    """Initiates the YouTube video upload."""
    merged_video_path = session.get('merged_video_path')
    video_title = request.json.get('video_title', 'My AI Generated Video')
    video_description = request.json.get('video_description', 'A video generated with AI narration.')

    if not merged_video_path or not os.path.exists(merged_video_path):
        return jsonify({'error': 'Merged video not found. Please merge first.'}), 400

    # In a real app, you'd handle YouTube OAuth here or retrieve a stored token
    # For now, this is a placeholder function in youtube_api.py
    try:
        def youtube_upload_progress():
            yield "data: {'status': 'in_progress', 'message': 'Starting YouTube upload...'}\n\n"
            # This function will yield progress messages
            for progress_info in upload_video_to_youtube(merged_video_path, video_title, video_description):
                yield f"data: {progress_info}\n\n"
            yield "data: {'status': 'complete', 'message': 'Upload to YouTube complete!'}\n\n"

        return Response(youtube_upload_progress(), mimetype='text/event-stream')

    except Exception as e:
        current_app.logger.error(f"YouTube upload failed: {str(e)}", exc_info=True)
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
                removed_count += 1
            except Exception as e:
                current_app.logger.error(f"Error cleaning up file {f_path}: {e}", exc_info=True)
    
    return jsonify({'message': f'Cleaned up {removed_count} temporary files.'})

