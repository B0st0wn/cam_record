from .recorder import start_recording, stop_recording

DOMAIN = "cam_record"
PROCESS_CACHE = {}

def setup(hass, config):
    def handle_start(call):
        stream_url = call.data["stream_url"]
        filename = call.data["filename"]
        process = start_recording(stream_url, filename)
        PROCESS_CACHE[stream_url] = process

    def handle_stop(call):
        stream_url = call.data["stream_url"]
        stop_recording(PROCESS_CACHE.get(stream_url))
        PROCESS_CACHE.pop(stream_url, None)

    hass.services.register(DOMAIN, "record_start", handle_start)
    hass.services.register(DOMAIN, "record_stop", handle_stop)
    return True
