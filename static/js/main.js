document.addEventListener('DOMContentLoaded', () => {
    // Get elements
    const uploadForm = document.getElementById('uploadForm');
    const videoFile = document.getElementById('videoFile');
    const uploadMessage = document.getElementById('uploadMessage');
    const scriptTextarea = document.getElementById('scriptTextarea');
    const generateSpeechBtn = document.getElementById('generateSpeechBtn');
    const speechMessage = document.getElementById('speechMessage');
    const videoPlayer = document.getElementById('videoPlayer');
    const audioPlayer = document.getElementById('audioPlayer');
    const mergeBtn = document.getElementById('mergeBtn'); // This is the old merge button, replaced by createNarratedVideoBtn
    const mergeProgressContainer = document.getElementById('mergeProgressBarContainer');
    const mergeProgressBar = document.getElementById('mergeProgressBar');
    const mergeProgressText = document.getElementById('mergeProgressText');
    const checkMergedVideoBtn = document.getElementById('checkMergedVideoBtn'); // Renamed to playMergedVideoBtn in HTML
    const mergedVideoPlayer = document.getElementById('mergedVideoPlayer');
    const youtubeUploadSection = document.getElementById('youtubeUploadSection');
    const youtubeTitle = document.getElementById('youtubeTitle');
    const youtubeDescription = document.getElementById('youtubeDescription');
    const youtubeUploadBtn = document.getElementById('youtubeUploadBtn');
    const youtubeProgressContainer = document.getElementById('youtubeProgressBarContainer');
    const youtubeProgressBar = document.getElementById('youtubeProgressBar');
    const youtubeProgressText = document.getElementById('youtubeProgressText');
    const statusMessage = document.getElementById('statusMessage'); // General status message, now mergeStatusMessage

    // New/Renamed elements for better clarity
    const playMergedVideoBtn = document.getElementById('playMergedVideoBtn');
    const downloadMergedVideoBtn = document.getElementById('downloadMergedVideoBtn');
    const mergeStatusMessage = document.getElementById('mergeStatusMessage');
    const createNarratedVideoBtn = document.getElementById('createNarratedVideoBtn'); // The new button

    // Elements for upload and analysis progress
    const uploadProgressBarContainer = document.getElementById('uploadProgressBarContainer');
    const uploadProgressBar = document.getElementById('uploadProgressBar');
    const uploadProgressText = document.getElementById('uploadProgressText');
    const analysisProgressBarContainer = document.getElementById('analysisProgressBarContainer');
    const analysisProgressBar = document.getElementById('analysisProgressBar');
    const analysisProgressText = document.getElementById('analysisProgressText');

    // Section containers to hide/show
    const uploadSection = document.getElementById('uploadSection');
    const scriptSection = document.getElementById('scriptSection');
    const scriptAudioSection = document.getElementById('scriptAudioSection');
    const speechSection = document.getElementById('speechSection');
    const videoPlaybackSection = document.getElementById('videoPlaybackSection');
    const mergeSection = document.getElementById('mergeSection'); // This is the merged video display section
    const mergedVideoPlaybackSection = document.getElementById('mergedVideoPlaybackSection'); // This section is now integrated into mergeSection
    const youtubeUploadDetailsSection = document.getElementById('youtubeUploadDetailsSection');

    // Speech feedback box element (to be created dynamically or added to HTML)
    let speechFeedbackBox = document.getElementById('speechFeedbackBox');


    // Helper to show/hide sections
    const showSection = (element) => {
        if (element) {
            element.classList.remove('hidden');
        } else {
            console.warn("Attempted to show a null element. Ensure all section IDs exist in index.html.");
        }
    };
    const hideSection = (element) => {
        if (element) {
            element.classList.add('hidden');
        } else {
            console.warn("Attempted to hide a null element. Ensure all section IDs exist in index.html.");
        }
    };

    // Helper for progress bar updates
    const updateProgressBar = (progressBarElement, textElement, progress, message) => {
        if (progressBarElement && textElement) {
            progressBarElement.style.width = `${progress}%`;
            progressBarElement.textContent = `${progress}%`;
            textElement.textContent = message;
            if (progress > 0 && progress < 100) {
                progressBarElement.parentNode.classList.remove('hidden');
            } else if (progress === 100) {
                progressBarElement.parentNode.classList.add('hidden'); // Hide on complete
            } else if (progress === 0 && message === '') { // Hide if reset
                progressBarElement.parentNode.classList.add('hidden');
            }
        } else {
            console.warn("Attempted to update a null progress bar element.");
        }
    };

    // Helper to enable/disable buttons and show spinner
    const setProcessingState = (button, messageElement, isProcessing, message = 'Processing...') => {
        if (!button) {
            console.warn("Attempted to set processing state on a null button element.");
            return;
        }

        // Store original width to maintain size
        if (!button.dataset.originalWidth) {
            button.dataset.originalWidth = button.offsetWidth + 'px';
        }

        if (isProcessing) {
            button.disabled = true;
            button.style.width = button.dataset.originalWidth; // Apply original width
            button.innerHTML = `<div class="spinner"></div><span class="loading-text">${message}</span>`;

            if (messageElement) {
                messageElement.className = 'message'; // Clear previous status
                messageElement.textContent = 'Please wait, this may take a moment...';
            }
        } else {
            button.disabled = false;
            button.style.width = ''; // Reset width
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText; // Restore original text
            } else {
                if (button.querySelector('.spinner')) {
                    button.innerHTML = 'Process'; // A generic fallback text
                }
            }
            if (messageElement) {
                messageElement.textContent = '';
            }
        }
    };

    // Helper to reset UI state
    const resetUI = () => {
        uploadMessage.textContent = '';
        if (scriptTextarea) scriptTextarea.value = ''; // Added null check here
        speechMessage.textContent = '';
        if (speechFeedbackBox) speechFeedbackBox.textContent = '';
        videoPlayer.src = '';
        audioPlayer.src = '';
        mergedVideoPlayer.src = '';
        youtubeTitle.value = '';
        youtubeDescription.value = '';

        // Reset all progress bars
        updateProgressBar(uploadProgressBar, uploadProgressText, 0, '');
        updateProgressBar(analysisProgressBar, analysisProgressText, 0, '');
        updateProgressBar(mergeProgressBar, mergeProgressText, 0, '');
        updateProgressBar(youtubeProgressBar, youtubeProgressText, 0, '');

        // Hide all major sections initially
        hideSection(uploadSection);
        hideSection(scriptSection);
        hideSection(scriptAudioSection);
        hideSection(speechSection);
        hideSection(videoPlaybackSection);
        hideSection(mergeSection); // Hide merged video section
        hideSection(youtubeUploadDetailsSection);

        // Make the upload section visible at the very beginning when the app loads fresh
        if (uploadSection) uploadSection.classList.remove('hidden');


        if (document.getElementById('uploadVideoBtn')) document.getElementById('uploadVideoBtn').disabled = false;
        if (videoFile) videoFile.disabled = false;
        if (generateSpeechBtn) generateSpeechBtn.disabled = true;
        if (createNarratedVideoBtn) createNarratedVideoBtn.disabled = true; // Disable new button
        if (mergeBtn) mergeBtn.disabled = true; // Old merge button, keep disabled
        if (playMergedVideoBtn) playMergedVideoBtn.disabled = true; // Play button for merged video
        if (downloadMergedVideoBtn) downloadMergedVideoBtn.classList.add('disabled'); // Disable download link
        if (youtubeUploadBtn) youtubeUploadBtn.disabled = true;
    };

    // Initial UI reset on page load
    resetUI();

    // Store original button texts
    document.querySelectorAll('button').forEach(btn => {
        if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.innerHTML;
        }
    });

    // 1. Video Upload & Analysis (now streamed)
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            console.log('Upload form submitted.');

            const file = videoFile.files[0];
            if (!file) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = 'Please select a video file.';
                console.log('No file selected.');
                return;
            }

            if (!file.type.startsWith('video/')) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = 'Please select a valid video file (e.g., MP4, WebM, MOV). Image files like WebP are not supported for video analysis.';
                console.error('Invalid file type selected:', file.type);
                videoFile.value = '';
                return;
            }

            console.log('File selected:', file.name, 'Type:', file.type);

            setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, true, 'Starting Upload...');
            uploadProgressBarContainer.classList.remove('hidden');
            analysisProgressBarContainer.classList.remove('hidden');

            updateProgressBar(uploadProgressBar, uploadProgressText, 0, 'File Upload: 0%');
            updateProgressBar(analysisProgressBar, analysisProgressText, 0, 'Analysis: Initializing...');

            const formData = new FormData();
            formData.append('video', file);

            let es;
            try {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload_video', true);

                xhr.upload.onprogress = function(event) {
                    if (event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        updateProgressBar(uploadProgressBar, uploadProgressText, percentComplete, `File Upload: ${percentComplete.toFixed(1)}%`);
                    }
                };

                xhr.onload = function() {
                    if (xhr.status === 200) {
                        const uploadResponseData = JSON.parse(xhr.responseText);
                        if (uploadResponseData.status === 'success' && uploadResponseData.unique_filename) {
                            updateProgressBar(uploadProgressBar, uploadProgressText, 100, 'File Upload: Complete');
                            uploadMessage.className = 'message success';
                            uploadMessage.textContent = uploadResponseData.message;

                            es = new EventSource(`/stream_analysis_progress?video_filename=${encodeURIComponent(uploadResponseData.unique_filename)}`);

                            es.onmessage = (event) => {
                                const data = JSON.parse(event.data);
                                if (data.status === 'in_progress') {
                                    updateProgressBar(analysisProgressBar, analysisProgressText, data.progress, data.message);
                                } else if (data.status === 'complete') {
                                    updateProgressBar(analysisProgressBar, analysisProgressText, 100, data.message);
                                    // Ensure data.script is an array before calling map
                                    if (scriptTextarea) {
                                        scriptTextarea.value = Array.isArray(data.script) ? data.script.map(item => `${item.time}: ${item.description}`).join('\n') : String(data.script);
                                    } else {
                                        console.error("scriptTextarea element not found when trying to set value.");
                                    }
                                    videoPlayer.src = uploadResponseData.video_url;

                                    hideSection(uploadSection);
                                    showSection(scriptSection);
                                    showSection(videoPlaybackSection);
                                    if (generateSpeechBtn) generateSpeechBtn.disabled = false;
                                    es.close();
                                } else if (data.status === 'error') {
                                    updateProgressBar(analysisProgressBar, analysisProgressText, 0, data.message);
                                    uploadMessage.className = 'message error';
                                    uploadMessage.textContent = data.message || 'Video analysis failed.';
                                    resetUI();
                                    es.close();
                                }
                            };

                            es.onerror = (error) => {
                                console.error('EventSource for analysis failed:', error);
                                updateProgressBar(analysisProgressBar, analysisProgressText, 0, 'Analysis failed due to connection error.');
                                uploadMessage.className = 'message error';
                                uploadMessage.textContent = 'Video analysis failed due to connection error.';
                                resetUI();
                                if (es) es.close();
                            };

                        } else {
                            uploadMessage.className = 'message error';
                            uploadMessage.textContent = uploadResponseData.error || 'Failed to get analysis stream.';
                            resetUI();
                            console.error('Upload failed with server response:', uploadResponseData);
                        }
                    } else {
                        uploadMessage.className = 'message error';
                        uploadMessage.textContent = `Server error during upload: ${xhr.statusText}`;
                        resetUI();
                        console.error('XHR Upload Error:', xhr.status, xhr.statusText);
                    }
                    setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, false);
                    console.log('Upload process finished (XHR).');
                };

                xhr.onerror = function() {
                    uploadMessage.className = 'message error';
                    uploadMessage.textContent = `Network error during XHR upload.`;
                    resetUI();
                    console.error('XHR Network Error.');
                    setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, false);
                };

                xhr.send(formData);


            } catch (error) {
                uploadMessage.className = 'message error';
                uploadMessage.textContent = `General error during upload/analysis setup: ${error.message}`;
                resetUI();
                console.error('General error during setup:', error);
                setProcessingState(document.getElementById('uploadVideoBtn'), uploadMessage, false);
            }
        });
    } else {
        console.error("Upload form element not found!");
    }


    // 2. Generate Speech
    if (generateSpeechBtn) {
        generateSpeechBtn.addEventListener('click', async () => {
            const scriptText = scriptTextarea.value;
            if (!scriptText.trim()) {
                speechMessage.className = 'message error';
                speechMessage.textContent = 'Script cannot be empty.';
                return;
            }

            // Ensure speechFeedbackBox exists or create it
            if (!speechFeedbackBox) {
                speechFeedbackBox = document.createElement('div');
                speechFeedbackBox.id = 'speechFeedbackBox';
                speechFeedbackBox.className = 'message speech-feedback-box hidden'; // Add new class
                generateSpeechBtn.parentNode.insertBefore(speechFeedbackBox, generateSpeechBtn.nextSibling);
            }
            speechFeedbackBox.classList.remove('hidden'); // Show it
            speechFeedbackBox.className = 'message speech-feedback-box'; // Reset class
            speechFeedbackBox.textContent = ''; // Clear previous messages

            setProcessingState(generateSpeechBtn, speechFeedbackBox, true, 'Generating Speech...');
            if (audioPlayer) audioPlayer.src = '';
            hideSection(scriptAudioSection); // Hide audio section initially

            try {
                // Now, use standard fetch POST to a blocking backend route
                const response = await fetch('/generate_speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ script_text: scriptText })
                });
                const data = await response.json();

                if (response.ok && data.status === 'complete') {
                    speechFeedbackBox.className = 'message speech-feedback-box success';
                    speechFeedbackBox.textContent = data.message;
                    if (audioPlayer) audioPlayer.src = data.audio_url;
                    showSection(scriptAudioSection); // Show audio section on complete
                    // Enable Create Narrated Video button
                    if (createNarratedVideoBtn) {
                        createNarratedVideoBtn.disabled = false;
                        createNarratedVideoBtn.classList.remove('disabled'); // Ensure green button is not disabled visually
                    }
                } else {
                    // Handle error from blocking response
                    speechFeedbackBox.className = 'message speech-feedback-box error';
                    speechFeedbackBox.textContent = data.message || 'Speech generation failed.';
                    console.error('Speech generation failed:', data);
                }
            } catch (error) {
                speechFeedbackBox.className = 'message speech-feedback-box error';
                speechFeedbackBox.textContent = `Network error: ${error.message}`;
                console.error('Network error during speech generation:', error);
            } finally {
                setProcessingState(generateSpeechBtn, speechFeedbackBox, false);
                // Optionally hide the speech feedback box after a short delay
                setTimeout(() => {
                    if (speechFeedbackBox) speechFeedbackBox.classList.add('hidden');
                }, 3000);
            }
        });
    } else {
        console.error("Generate Speech button not found!");
    }


    // 3. Create Narrated Video (Merge Video and Audio)
    if (createNarratedVideoBtn) {
        createNarratedVideoBtn.addEventListener('click', async () => {
            setProcessingState(createNarratedVideoBtn, mergeStatusMessage, true, 'Merging Video...');
            showSection(mergeSection); // Show the merged video preview section
            updateProgressBar(mergeProgressBar, mergeProgressText, 0, 'Starting merge...');

            try {
                // Use EventSource for streaming progress from the backend (now a GET route)
                const es = new EventSource('/merge_video_audio');

                es.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.status === 'in_progress') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, data.progress, data.message);
                    } else if (data.status === 'complete') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, 100, data.message);
                        mergeStatusMessage.className = 'message success';
                        mergeStatusMessage.textContent = data.message;
                        if (mergedVideoPlayer) mergedVideoPlayer.src = data.merged_video_url;

                        // Enable play and download buttons for merged video
                        if (playMergedVideoBtn) playMergedVideoBtn.disabled = false;
                        if (downloadMergedVideoBtn) {
                            downloadMergedVideoBtn.href = data.merged_video_url;
                            downloadMergedVideoBtn.classList.remove('disabled');
                        }

                        // Show the merged video section with slide-in effect
                        mergeSection.classList.add('active'); // Trigger slide-in

                        // Enable YouTube upload button
                        if (youtubeUploadBtn) youtubeUploadBtn.disabled = false;
                        es.close();
                    } else if (data.status === 'error') {
                        updateProgressBar(mergeProgressBar, mergeProgressText, 0, data.message);
                        mergeStatusMessage.className = 'message error';
                        mergeStatusMessage.textContent = data.message || 'Video merge failed.';
                        console.error('Video merge failed:', data);
                        // On error, hide the merge section or keep it with error message
                        mergeSection.classList.remove('active'); // Hide slide-in on error
                        es.close();
                    }
                };
                es.onerror = (error) => {
                    console.error('EventSource failed:', error);
                    updateProgressBar(mergeProgressBar, mergeProgressText, 0, 'Merge failed due to connection error.');
                    mergeStatusMessage.className = 'message error';
                    mergeStatusMessage.textContent = 'Video merge failed due to connection error.';
                    mergeSection.classList.remove('active'); // Hide slide-in on error
                    if (es) es.close(); // Ensure EventSource is closed
                };

            } catch (error) {
                mergeStatusMessage.className = 'message error';
                mergeStatusMessage.textContent = `Network error: ${error.message}`;
                console.error('Network error during merge:', error);
                mergeSection.classList.remove('active');
            } finally {
                setProcessingState(createNarratedVideoBtn, mergeStatusMessage, false);
            }
        });
    } else {
        console.error("Create Narrated Video button not found!");
    }


    // 4. Play Merged Video (Renamed from Check Merged Video)
    if (playMergedVideoBtn) {
        playMergedVideoBtn.addEventListener('click', async () => {
            if (mergedVideoPlayer && mergedVideoPlayer.src) {
                mergedVideoPlayer.play();
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
        console.error("Play Merged Video button not found!");
    }


    // 5. Upload to YouTube
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
            showSection(youtubeUploadSection);
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
                        fetch('/cleanup_files', { method: 'POST' });
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

                // This fetch call is to trigger the YouTube upload with title/description
                // and should be separate from the EventSource for progress.
                // The backend /upload_to_youtube is a POST route, so this is correct.
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
