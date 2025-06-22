import json
import time

def generate_progress_stream(total_steps, delay=0.5):
    """
    A simple generator for simulating progress updates for Server-Sent Events.
    
    Args:
        total_steps (int): The total number of steps for the progress.
        delay (float): The delay in seconds between each progress update.

    Yields:
        str: A JSON string formatted for SSE, indicating progress percentage.
    """
    for i in range(total_steps):
        progress_percentage = int(((i + 1) / total_steps) * 100)
        yield f"data: {json.dumps({'status': 'in_progress', 'progress': progress_percentage, 'message': f'Processing: {progress_percentage}% complete'})}\n\n"
        time.sleep(delay)
    yield f"data: {json.dumps({'status': 'complete', 'message': 'Operation complete!'})}\n\n"

