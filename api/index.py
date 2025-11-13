import subprocess
import sys
import threading
import time

# Start Streamlit server in a background thread
def start_streamlit():
    subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

# Ensure Streamlit starts only once
started = False

def handler(request, response):
    global started
    if not started:
        threading.Thread(target=start_streamlit, daemon=True).start()
        started = True
        time.sleep(2)

    # Redirect Vercel route to Streamlit's internal port
    response.status_code = 302
    response.headers["Location"] = "http://localhost:8501"
    return "Redirecting to Streamlit..."
