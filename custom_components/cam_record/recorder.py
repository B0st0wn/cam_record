import subprocess

def start_recording(stream_url, filename):
    cmd = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", stream_url,
        "-vcodec", "copy",
        "-acodec", "aac",
        "-y",
        filename
    ]
    return subprocess.Popen(cmd)

def stop_recording(process):
    if process and process.poll() is None:
        process.terminate()
