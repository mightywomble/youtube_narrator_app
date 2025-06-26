#!/bin/bash

# This script automates the setup and execution of the YouTube Narrator application.
# It performs cleanup, virtual environment creation, dependency installation,
# and finally runs the main application file.

# --- Script Configuration ---
# Define the name of your project directory.
# This script is now designed to be run *from within* this directory.
# Therefore, PROJECT_DIRECTORY can be set to '.' (current directory) or left as is
# if you want to keep the original directory name for reference, but the initial 'cd' is removed.
PROJECT_DIRECTORY="youtube_narrator_app" # This variable is mostly for descriptive comments now.

# --- Step 1: (Removed initial 'cd' since the script is expected to run from here) ---
echo "Executing script from the current directory: $(pwd)"
# No 'cd' command needed here as the script is now intended to be run
# directly from within the youtube_narrator_app directory.

# --- Step 2: Deactivate any currently active Python virtual environment ---
echo "Deactivating any active Python virtual environment (if one exists)..."
# Check if the 'deactivate' command is available in the shell.
# 'type -t deactivate' checks if 'deactivate' is an alias, keyword, function, or file.
if type -t deactivate &> /dev/null; then
    deactivate
    echo "Virtual environment deactivated."
else
    echo "No active virtual environment found or 'deactivate' command not available."
fi

# --- Step 3: Remove the existing virtual environment directory ---
echo "Removing existing 'venv' directory..."
# Check if the 'venv' directory exists inside the project folder
if [ -d "venv" ]; then
  rm -rf venv
  echo "'venv' directory removed successfully."
else
  echo "'venv' directory not found, skipping removal."
fi

# --- Step 4: Remove all __pycache__ directories within the project ---
echo "Cleaning up all '__pycache__' directories within the project..."
# 'find .' searches from the current directory (which is now youtube_narrator_app).
# '-name "__pycache__"' finds directories named __pycache__.
# '-type d' ensures only directories are targeted.
# '-exec rm -rf {} +' executes 'rm -rf' on found directories.
find . -name "__pycache__" -type d -exec rm -rf {} +
echo "__pycache__ directories cleaned."

# --- Step 5: Create a new Python virtual environment ---
echo "Creating a new Python virtual environment in 'venv'..."
# Create a new virtual environment using python3
python3 -m venv venv
# Check the exit status of the previous command. If non-zero, an error occurred.
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment. Please ensure 'python3' is installed and in your PATH."
    exit 1
fi
echo "Virtual environment created successfully."

# --- Step 6: Activate the new virtual environment ---
echo "Activating the new virtual environment..."
# Source the activate script to activate the virtual environment
source venv/bin/activate
# Check if activation was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment. Exiting."
    exit 1
fi
echo "Virtual environment activated."

# --- Step 7: Install dependencies from requirements.txt ---
echo "Installing dependencies from 'requirements.txt'..."
# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    # Check if pip installation was successful
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies. Please check 'requirements.txt' and your internet connection."
        # Attempt to deactivate venv before exiting
        deactivate
        exit 1
    fi
    echo "Dependencies installed successfully."
else
    echo "Error: 'requirements.txt' not found in the current directory ($(pwd))."
    echo "Please ensure 'requirements.txt' exists to install necessary dependencies."
    # Attempt to deactivate venv before exiting
    deactivate
    exit 1
fi

# --- Step 8: Run the main application file (app.py) ---
echo "Starting the application 'app.py'..."
# Check if app.py exists
if [ -f "app.py" ]; then
    python3 app.py
    # Note: If 'app.py' runs a web server or a long-running process,
    # this script will wait for it to finish.
    # If you want it to run in the background, you can add '&' after 'python3 app.py'
    # (e.g., 'python3 app.py & disown'). However, this might complicate logging
    # and error handling within the script itself.
else
    echo "Error: 'app.py' not found in the current directory ($(pwd))."
    echo "Please ensure 'app.py' exists to run the application."
    # Attempt to deactivate venv before exiting
    deactivate
    exit 1
fi

echo "Script execution complete."
