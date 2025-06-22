import os

# Base configuration values
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
TESTING = False
ENV = os.getenv('FLASK_ENV', 'development')

# Placeholder for sensitive keys. THESE SHOULD BE SET IN instance/config.py OR ENVIRONMENT VARIABLES.
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') # For API access, if needed
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID') # For OAuth
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET') # For OAuth

# Gemini API key (for text-to-speech) - will be handled within the client-side fetch or backend if model is non-flash
# No direct placeholder here as it's often handled in JS or via backend fetch with empty key.
