import subprocess
from typing import Optional


def start_recording(stream_url: str, filename: str) -> subprocess.Popen:
    """Start an ffmpeg process that records the given stream to filename.

    Uses TCP for RTSP, copies video to avoid re-encode, and encodes audio to AAC
    for MP4 compatibility. The process stdin is opened so we can send a
    graceful quit command ("q") to finalize container headers on stop.
    """
    cmd = [
        "ffmpeg",
        "-rtsp_transport",
        "tcp",
        "-i",
        stream_url,
        "-vcodec",
        "copy",
        "-acodec",
        "aac",
        "-y",
        filename,
    ]
    # Open stdin for graceful stop; avoid spamming logs by not inheriting stdio.
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
    )


def stop_recording(process: Optional[subprocess.Popen]) -> None:
    """Stop ffmpeg gracefully (finalize MP4), with safe fallbacks.

    - First, try sending "q" to ffmpeg stdin which requests a clean shutdown.
    - Then wait briefly. If still running, terminate, then kill as a last resort.
    """
    if not process or process.poll() is not None:
        return

    # Try graceful quit via stdin
    try:
        if process.stdin:
            process.stdin.write(b"q")
            process.stdin.flush()
    except Exception:
        pass

    try:
        process.wait(timeout=5)
        return
    except Exception:
        pass

    # Fallback: terminate and then kill if needed
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass
