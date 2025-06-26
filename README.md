AI Video Narrator App
This web application helps content creators produce YouTube videos by automating the narration process. Users can upload a video, have its content analyzed by AI to generate a script, convert that script into natural language speech, and then merge the audio with the original video. The final narrated video can then be prepared for YouTube upload.

Features
Video Upload: Upload video files (e.g., WEBM, MOV, MP4) to the application.

AI Video Analysis: Utilizes Google's Gemini 1.5 Flash model to analyze video content, detect scenes, and generate a timestamped script describing what is happening.

Script Editing: Display the generated script for user review and editing.

Text-to-Speech (TTS): Converts the script text into natural-sounding speech using ElevenLabs API, with a configurable male voice.

Video & Audio Merging: Uses FFmpeg to seamlessly merge the original video file with the AI-generated audio track.

YouTube Upload Integration (Placeholder): Provides a button to initiate video upload to YouTube with customizable title and description (requires further YouTube API OAuth implementation).

Real-time Progress: Displays dynamic progress bars for video upload, AI analysis, and video merging.

User-friendly Interface: Clean and responsive web interface built with Flask, HTML, CSS, and JavaScript.

Technologies Used
Backend: Python (Flask)

Frontend: HTML, CSS, JavaScript (with XHR/EventSource for dynamic updates)

Video Processing:

OpenCV: For video file handling and properties.

FFmpeg: Command-line tool for video/audio merging (must be installed on the server).

Artificial Intelligence:

Google Gemini API (gemini-1.5-flash): For video content analysis and script generation.

ElevenLabs API: For high-quality Text-to-Speech (TTS) synthesis.

Dependency Management: pip, venv

Server: Gunicorn (for production deployment), Werkzeug (Flask's development server)

Setup and Installation
Follow these steps to get the application running on your local machine or Linux server.

1. Clone the Repository (or create project structure)
If you have a project structure already, skip to step 2. Otherwise, you can use the setup_app.sh script (provided separately in our conversation history) to create the basic file structure.

# Example: If you have the setup_app.sh script
./setup_app.sh
cd youtube_narrator_app

2. Install FFmpeg
FFmpeg is essential for video processing (audio extraction and merging).

On Ubuntu/Debian:

sudo apt update
sudo apt install ffmpeg

On macOS (using Homebrew):

brew install ffmpeg

On Windows: Download from the official FFmpeg website and add it to your system's PATH.

3. Set up Python Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies.

# Navigate to your project root directory
cd /path/to/your/youtube_narrator_app

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: .\venv\Scripts\activate.bat or .\venv\Scripts\Activate.ps1

4. Install Python Dependencies
With your virtual environment activated, install the required Python libraries.

pip install -r requirements.txt

5. Configure API Keys
You need API keys for Google Gemini and ElevenLabs. These should be stored securely and NOT committed to your public GitHub repository.

Google Gemini API Key:

Get your key from Google AI Studio.

ElevenLabs API Key:

Get your key from your ElevenLabs account page.

YouTube API Keys (Optional, for full YouTube upload functionality):

Create a project in Google Cloud Console.

Enable the YouTube Data API v3.

Create OAuth 2.0 Client IDs and API keys if you plan to implement full user-specific YouTube uploads.

How to provide keys to the application (choose ONE):

a.  Environment Variables (Recommended for Production):
Set these in your terminal session before running the app, or in a .env file (which python-dotenv will load).
bash export SECRET_KEY="YOUR_FLASK_APP_SECRET_KEY_HERE" # Generate a long, random string! export GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE" export ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY_HERE" # export YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY_HERE" # export YOUTUBE_CLIENT_ID="YOUR_YOUTUBE_OAUTH_CLIENT_ID_HERE" # export YOUTUBE_CLIENT_SECRET="YOUR_YOUTUBE_OAUTH_CLIENT_SECRET_HERE"

b.  instance/config.py (Recommended for Local Development):
Create a file named config.py inside the instance/ directory of your project. Ensure instance/ is in your .gitignore file.
python # youtube_narrator_app/instance/config.py SECRET_KEY = 'your_super_secret_and_random_flask_key_here_replace_this' GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE' ELEVENLABS_API_KEY = 'YOUR_ELEVENLABS_API_KEY_HERE' YOUTUBE_API_KEY = 'AIzaSy_YOUR_YOUTUBE_API_KEY_HERE_IF_NEEDED' YOUTUBE_CLIENT_ID = 'YOUR_YOUTUBE_OAUTH_CLIENT_ID_HERE.apps.googleusercontent.com' YOUTUBE_CLIENT_SECRET = 'YOUR_YOUTUBE_OAUTH_CLIENT_SECRET_HERE' U

6. Run the Flask Application
# Ensure your virtual environment is active
# cd /path/to/your/youtube_narrator_app
# source venv/bin/activate

# Run the Flask app on port 5005 (accessible from network)
python3 app.py

The application should now be running at http://0.0.0.0:5005 (or http://127.0.0.1:5005 if accessed locally).

Usage
Upload Video: On the home page, select a video file (MP4, WebM, MOV recommended) and click "Upload Video & Analyze". You will see progress bars for file upload and AI analysis.

Review Script: Once analysis is complete, the original video and the AI-generated script will appear side-by-side. Review and edit the script as needed.

Convert to Speech: Click "Convert Script to Speech". A progress indicator will show, and once complete, an audio player will appear under the video.

Create Narrated Video: Click the green "Create Narrated Video" button. This will merge the original video with the generated audio. A progress bar will show, and upon completion, a new section will slide in from the right, displaying the merged video with play and download options.

Upload to YouTube: (Future functionality) Enter a title and description, then click "Upload to YouTube".

Troubleshooting
ModuleNotFoundError:

Ensure you are running python3 app.py from the youtube_narrator_app root directory.

Verify that all __init__.py files exist in routes/, services/, and utils/ directories.

Confirm your virtual environment is activated.

TypeError: ... unexpected keyword argument 'proxies' or ImportError for elevenlabs:

Perform a very clean reinstall of your dependencies:

deactivate
rm -rf venv
find . -name "__pycache__" -exec rm -rf {} + # From project root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Ensure elevenlabs==1.0.0b0 and httpx==0.25.2 (or compatible versions) are specified in requirements.txt.

RuntimeError: Working outside of request context (for session access):

Ensure your routes/main_routes.py is fully updated to the latest version provided, especially the /generate_speech route, which is now a blocking (non-streaming) call to avoid this.

SyntaxError: invalid syntax in .py files:

This usually means you copied markdown code fences (```python or ` ```) from the AI's response into your Python files. Remove these lines.

SyntaxError: Unexpected token 'd' or 405 Method Not Allowed for /generate_speech:

This means your static/js/main.js is still expecting an SSE stream from /generate_speech, but the backend now sends a blocking JSON response. Update static/js/main.js to the latest version provided, ensuring it uses fetch and response.json() for this endpoint.

400 Bad Request or 404 Not Found from Gemini/ElevenLabs:

Double-check your API keys in instance/config.py or environment variables. Ensure no typos.

Verify the API key has the correct permissions in your Google Cloud/ElevenLabs account.

For Gemini, ensure the model name (gemini-1.5-flash) is correct and not deprecated.

For Gemini File API, ensure the file status becomes ACTIVE (the code has a wait_for_file_active function for this).

Error removing temporary directory ... No such file or directory:

This is often a minor warning during cleanup and usually doesn't prevent the core functionality from working. It means the directory was already removed or didn't exist when os.rmdir was called.

R_
