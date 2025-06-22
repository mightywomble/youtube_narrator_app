document.addEventListener('DOMContentLoaded', () => {
    // Get elements
    const uploadForm = document.getElementById('uploadForm');
    const videoFile = document.getElementById('videoFile');
    const uploadMessage = document.getElementById('uploadMessage');
    const scriptTextarea = document.getElementById('scriptText');
    const generateSpeechBtn = document.getElementById('generateSpeechBtn');
    const speechMessage = document.getElementById('speechMessage');
    const videoPlayer = document.getElementById('videoPlayer');
    const audioPlayer = document.getElementById('audioPlayer');
    const mergeBtn = document.getElementById('mergeBtn');
    const mergeProgressContainer = document.getElementById('mergeProgressBarContainer');
    const mergeProgressBar = document.getElementById('mergeProgressBar');
    const mergeProgressText = document.getElementById('mergeProgressText');
    const checkMergedVideoBtn = document.getElementById('checkMergedVideoBtn');
    const mergedVideoPlayer = document.getElementById('mergedVideoPlayer');
    const youtubeUploadSection = document.getElementById('youtubeUploadSection');
    const youtubeTitle = document.getElementById('youtubeTitle');
    const youtubeDescription = document.getElementById('youtubeDescription');
    const youtubeUploadBtn = document.getElementById('youtubeUploadBtn');
    const youtubeProgressContainer = document.getElementById('youtubeProgressBarContainer');
    const youtubeProgressBar = document.getElementById('youtubeProgressBar');
    const youtubeProgressText = document.getElementById('youtubeProgressText');
    const statusMessage = document.getElementById('statusMessage');

    // Section containers to hide/show - Ensure these IDs exist in index.html!
    const scriptSection = document.getElementById('scriptSection');
    const speechSection = document.getElementById('speechSection');
    const videoPlaybackSection = document.getElementById('videoPlaybackSection');
    const mergeSection = document.getElementById('mergeSection');
    const mergedVideoPlaybackSection = document.getElementById('mergedVideoPlaybackSection');
    const youtubeUploadDetailsSection = document.getElementById('youtubeUploadDetailsSection');


    // Helper to show/hide sections
    const showSection = (element) => {
        if (element) { // Add null check
            element.classList.remove('hidden');
        } else {
            console.warn("Attempted to show a null element. Ensure all section IDs exist in index.html.");
        }
    };
    const hideSection = (element) => {
        if (element) { // Add null check
            element.classList.add('hidden');
        } else {
            console.warn("Attempted to hide a null element. Ensure all section IDs exist in index.html.");
        }
    };

    // Helper for progress bar updates - DEFINED FIRST
    const updateProgressBar = (progressBarElement, textElement, progress, message) => {
        if (progressBarElement && textElement) { // Add null checks
            progressBarElement.style.width = `${progress}%`;
            progressBarElement.textContent = `${progress}%`;
            textElement.textContent = message;
            if (progress > 0 && progress < 100) {
                progressBarElement.parentNode.classList.remove('hidden');
            } else if (progress === 100) {
                // Can choose to hide or show "Complete"
                progressBarElement.parentNode.classList.add('hidden'); // Hide on complete
            }
        } else {
            console.warn("Attempted to update a null progress bar element.");
        }
    };

    // Helper to enable/disable buttons and show spinner - DEFINED AFTER updateProgressBar
    const setProcessingState = (button, messageElement, isProcessing, message = 'Processing...') => {
        if (!button) { // Null check for button
            console.warn("Attempted to set processing state on a null button element.");
            return;
        }

        if (isProcessing) {
            button.disabled = true;
            button.innerHTML = `<div class="spinner"></div><span class="loading-text">${message}</span>`;
            if (messageElement) {
                messageElement.className = 'message'; // Clear previous status
                messageElement.textContent = 'Please wait, this may take a moment...';
            }
        } else {
            button.disabled = false;
            // Only restore original text if it was stored
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            } else {
                // Fallback if originalText wasn't set, e.g., for elements created dynamically
                // Or if the button already had the spinner, just remove spinner
                if (button.querySelector('.spinner')) {
                     button.innerHTML = 'Process'; // A generic fallback text
                }
            }
            if (messageElement) {
                messageElement.textContent = '';
            }
        }
    };

    // Helper to reset UI state - DEFINED AFTER functions it calls
    const resetUI = () => {
        // Null checks added implicitly by showSection/hideSection/updateProgressBar
        uploadMessage.textContent = '';
        scriptTextarea.value = '';
        speechMessage.textContent = '';
        videoPlayer.src = '';
        audioPlayer.src = '';
        mergedVideoPlayer.src = '';
        youtubeTitle.value = '';
        youtubeDescription.value = '';
        
        // Ensure these elements are not null before calling updateProgressBar
        if (mergeProgressBar && mergeProgressText) {
            updateProgressBar(mergeProgressBar, mergeProgressText, 0, '');
        }
        if (youtubeProgressBar && youtubeProgressText) {
            updateProgressBar(youtubeProgressBar, youtubeProgressText, 0, '');
        }

        hideSection(scriptSection);
        hideSection(speechSection);
        hideSection(videoPlaybackSection);
        hideSection(mergeSection);
        hideSection(mergedVideoPlaybackSection);
        hideSection(youtubeUploadDetailsSection);

        // Ensure these button elements exist before accessing disabled property
        if (document.getElementById('uploadVideoBtn')) document.getElementById('uploadVideoBtn').disabled = false;
        if (videoFile) videoFile.disabled = false;
        if (generateSpeechBtn) generateSpeechBtn.disabled = true;
        if (mergeBtn) mergeBtn.disabled = true;
        if (checkMergedVideoBtn) checkMergedVideoBtn.disabled = true;
        if (youtubeUploadBtn) youtubeUploadBtn.disabled = true;
    };

    // Initial UI reset on page load
    resetUI();

    // Store original button texts
    document.querySelectorAll('button').forEach(btn => {
        // Ensure data-originalText is set only if it's not already,
        // to avoid overwriting the spinner text if resetUI runs again
        if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.innerHTML;
        }
    });

    // 1. Video Upload
    // Check if uploadForm exists before adding event listener
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // This is crucial for preventing default GET submission
            
            console.log('Upload form submitted.'); // Debugging log

            const file = videoFile.files[0];
            if (!file) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = 'Please select a video file.';
                console.log('No file selected.'); // Debugging log
                return;
            }

            // --- Frontend file type validation ---
            // Ensure the file is actually a video based on MIME type
            if (!file.type.startsWith('video/')) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = 'Please select a valid video file (e.g., MP4, WebM, MOV). Image files like WebP are not supported for video analysis.';
                console.error('Invalid file type selected:', file.type); // Debugging log
                // Clear the file input for re-selection
                videoFile.value = ''; 
                return;
            }
            // --- End frontend file type validation ---

            console.log('File selected:', file.name, 'Type:', file.type); // Debugging log

            const formData = new FormData();
            formData.append('video', file);

            setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, true, 'Uploading & Analyzing...');

            try {
                console.log('Sending POST request to /upload_video...'); // Debugging log
                const response = await fetch('/upload_video', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (response.ok) {
                    uploadMessage.className = 'message success';
                    uploadMessage.textContent = data.message;
                    scriptTextarea.value = data.script.map(item => `${item.time}: ${item.description}`).join('\n');
                    videoPlayer.src = data.video_url;
                    
                    showSection(scriptSection);
                    showSection(videoPlaybackSection);
                    if (generateSpeechBtn) generateSpeechBtn.disabled = false;
                } else {
                    uploadMessage.className = 'message error';
                    uploadMessage.textContent = data.error || 'Failed to upload video.';
                    resetUI();
                    console.error('Upload failed with server response:', data); // Debugging log
                }
            } catch (error) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = `Network error: ${error.message}`;
                resetUI();
                console.error('Network error during upload:', error); // Debugging log
            } finally {
                setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, false);
                console.log('Upload process finished.'); // Debugging log
            }
        });
    } else {
        console.error("Upload form element not found!");
    }


    // 2. Generate Speech
    // Check if generateSpeechBtn exists before adding event listener
    if (generateSpeechBtn) {
        generateSpeechBtn.addEventListener('click', async () => {
            const scriptText = scriptTextarea.value;
            if (!scriptText.trim()) {
                speechMessage.className = 'message error';
                speechMessage.textContent = 'Script cannot be empty.';
                return;
            }
            
            setProcessingState(generateSpeechBtn, speechMessage, true, 'Generating Speech...');
            showSection(speechSection); // Show speech section
            if (audioPlayer) audioPlayer.src = ''; // Clear previous audio
            
            try {
                const es = new EventSource('/generate_speech');
                es.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.status === 'in_progress') {
                        speechMessage.className = 'message';
                        speechMessage.textContent = data.message;
                    } else if (data.status === 'complete') {
                        speechMessage.className = 'message success';
                        speechMessage.textContent = data.message;
                        if (audioPlayer) audioPlayer.src = data.audio_url;
                        es.close();
                        if (mergeBtn) mergeBtn.disabled = false;
                    } else if (data.status === 'error') {
                        speechMessage.className = 'message error';
                        speechMessage.textContent = data.message || 'Speech generation failed.';
                        es.close();
                    }
                };
                es.onerror = (error) => {
                    console.error('EventSource failed:', error);
                    speechMessage.className = 'message error';
                    speechMessage.textContent = 'Speech generation failed due to connection error.';
                    es.close();
                };

                await fetch('/generate_speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ script_text: scriptText })
                });

            } catch (error) {
                speechMessage.className = 'message error';
                speechMessage.textContent = `Network error: ${error.message}`;
            } finally {
                setProcessingState(generateSpeechBtn, speechMessage, false);
            }
        });
    } else {
        console.error("Generate Speech button not found!");
    }


    // 3. Merge Video and Audio
    // Check if mergeBtn exists before adding event listener
    if (mergeBtn) {
        mergeBtn.addEventListener('click', async () => {
            setProcessingState(mergeBtn, statusMessage, true, 'Merging Video...');
            showSection(mergeSection); // Ensure progress bar container is visible
            updateProgressBar(mergeProgressBar, mergeProgressText, 0, 'Starting merge...');

            try {
                const es = new EventSource('/merge_video_audio');
                es.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.status === 'in_progress') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, data.progress, data.message);
                    } else if (data.status === 'complete') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, 100, data.message);
                        statusMessage.className = 'message success';
                        statusMessage.textContent = data.message;
                        if (mergedVideoPlayer) mergedVideoPlayer.src = data.merged_video_url;
                        showSection(mergedVideoPlaybackSection);
                        if (checkMergedVideoBtn) checkMergedVideoBtn.disabled = false;
                        es.close();
                    } else if (data.status === 'error') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, 0, data.message);
                        statusMessage.className = 'message error';
                        statusMessage.textContent = data.message || 'Video merge failed.';
                        es.close();
                    }
                };
                es.onerror = (error) => {
                    console.error('EventSource failed:', error);
                    statusMessage.className = 'message error';
                    statusMessage.textContent = 'Video merge failed due to connection error.';
                    es.close();
                };

                await fetch('/merge_video_audio', { method: 'POST' });

            } catch (error) {
                statusMessage.className = 'message error';
                statusMessage.textContent = `Network error: ${error.message}`;
            } finally {
                setProcessingState(mergeBtn, statusMessage, false);
            }
        });
    } else {
        console.error("Merge button not found!");
    }


    // 4. Check Merged Video (Play)
    // Check if checkMergedVideoBtn exists before adding event listener
    if (checkMergedVideoBtn) {
        checkMergedVideoBtn.addEventListener('click', () => {
            if (mergedVideoPlayer && mergedVideoPlayer.src) {
                mergedVideoPlayer.play();
                // Show the YouTube upload section after playing the merged video for confirmation
                showSection(youtubeUploadDetailsSection);
                if (youtubeUploadBtn) youtubeUploadBtn.disabled = false;
                statusMessage.textContent = "Review the merged video. If it looks good, you can proceed to YouTube upload.";
                statusMessage.className = 'message success';
            } else {
                statusMessage.className = 'message error';
                statusMessage.textContent = 'No merged video to play.';
            }
        });
    } else {
        console.error("Check Merged Video button not found!");
    }


    // 5. Upload to YouTube
    // Check if youtubeUploadBtn exists before adding event listener
    if (youtubeUploadBtn) {
        youtubeUploadBtn.addEventListener('click', async () => {
            const title = youtubeTitle.value.trim();
            const description = youtubeDescription.value.trim();

            if (!title) {
                statusMessage.className = 'message error';
                statusMessage.textContent = 'Please enter a video title.';
                return;
            }

            setProcessingState(youtubeUploadBtn, statusMessage, true, 'Uploading to YouTube...');
            showSection(youtubeUploadSection); // Show upload progress bar container
            updateProgressBar(youtubeProgressBar, youtubeProgressText, 0, 'Starting YouTube upload...');

            try {
                const es = new EventSource('/upload_to_youtube');
                es.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.status === 'in_progress') {
                        updateProgressBar(youtubeProgressBar, youtubeProgressText, data.progress, data.message);
                    } else if (data.status === 'complete') {
                        updateProgressBar(youtubeProgressBar, youtubeProgressText, 100, data.message);
                        statusMessage.className = 'message success';
                        statusMessage.textContent = data.message;
                        es.close();
                        // Optionally clean up files after successful upload
                        fetch('/cleanup_files', { method: 'POST' });
                        // Provide a link to the uploaded video if the real API returned it
                    } else if (data.status === 'error') {
                        updateProgressBar(youtubeProgressBar, youtubeProgressText, 0, data.message);
                        statusMessage.className = 'message error';
                        statusMessage.textContent = data.message || 'YouTube upload failed.';
                        es.close();
                    }
                };
                es.onerror = (error) => {
                    console.error('EventSource failed:', error);
                    statusMessage.className = 'message error';
                    statusMessage.textContent = 'YouTube upload failed due to connection error.';
                    es.close();
                };

                await fetch('/upload_to_youtube', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ video_title: title, video_description: description })
                });

            } catch (error) {
                statusMessage.className = 'message error';
                statusMessage.textContent = `Network error: ${error.message}`;
            } finally {
                setProcessingState(youtubeUploadBtn, statusMessage, false);
            }
        });
    } else {
        console.error("YouTube Upload button not found!");
    }
});
