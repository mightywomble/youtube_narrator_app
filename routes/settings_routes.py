import os
from flask import Blueprint, request, render_template, current_app, jsonify

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def show_settings():
    """Renders the settings page."""
    # Pass current (or dummy) values for display
    # These values will come from app.config which is loaded from environment variables or config.py/instance/config.py
    return render_template('settings.html',
                           gemini_key_set=bool(current_app.config.get('GEMINI_API_KEY')),
                           elevenlabs_key_set=bool(current_app.config.get('ELEVENLABS_API_KEY')), # New: Check for ElevenLabs key
                           youtube_api_key_set=bool(current_app.config.get('YOUTUBE_API_KEY')),
                           youtube_client_id_set=bool(current_app.config.get('YOUTUBE_CLIENT_ID')))

@settings_bp.route('/save_settings', methods=['POST'])
def save_settings():
    """Saves API key settings."""
    # In this simplified setup, this route primarily demonstrates receipt of data.
    # The keys are not persistently saved by this function.
    # For actual persistence, they should be set as environment variables or in instance/config.py
    # and the Flask app restarted to pick them up, or a more complex secure config management system used.

    gemini_api_key = request.form.get('gemini_api_key')
    elevenlabs_api_key = request.form.get('elevenlabs_api_key') # New: Get ElevenLabs key from form
    youtube_api_key = request.form.get('youtube_api_key')
    youtube_client_id = request.form.get('youtube_client_id')
    youtube_client_secret = request.form.get('youtube_client_secret')

    # For demonstration: Update current_app.config in runtime.
    # This is volatile and will be lost on app restart.
    current_app.config['GEMINI_API_KEY'] = gemini_api_key
    current_app.config['ELEVENLABS_API_KEY'] = elevenlabs_api_key # New: Update ElevenLabs key in config
    current_app.config['YOUTUBE_API_KEY'] = youtube_api_key
    current_app.config['YOUTUBE_CLIENT_ID'] = youtube_client_id
    current_app.config['YOUTUBE_CLIENT_SECRET'] = youtube_client_secret

    response_message = "Settings received and temporarily applied. For permanent storage, set as environment variables or in instance/config.py."
    if gemini_api_key:
        response_message += " Gemini Key: Provided."
    if elevenlabs_api_key: # New: Check ElevenLabs key
        response_message += " ElevenLabs Key: Provided."
    if youtube_api_key:
        response_message += " YouTube API Key: Provided."
    if youtube_client_id:
        response_message += " YouTube Client ID: Provided."
    if youtube_client_secret:
        response_message += " YouTube Client Secret: Provided."

    return jsonify({'message': response_message, 'status': 'success'})
