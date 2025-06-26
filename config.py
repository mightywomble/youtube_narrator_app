import os

# Base configuration values
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
TESTING = False
ENV = os.getenv('FLASK_ENV', 'development')

# Placeholder for sensitive keys. THESE SHOULD BE SET IN instance/config.py OR ENVIRONMENT VARIABLES.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY') # New: Placeholder for ElevenLabs API Key
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') # For API access, if needed
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID') # For OAuth
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET') # For OAuth

# GOOGLE_APPLICATION_CREDENTIALS is removed as Google Cloud TTS is no longer used.
