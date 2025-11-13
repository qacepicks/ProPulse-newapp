import subprocess
import sys

def handler(request, response):
    # Start streamlit app if not already running
    subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    response.status_code = 200
    return "PropPulse Streamlit backend running"
