import logging
from typing import Any, Dict

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components import camera as ha_camera

from .recorder import start_recording, stop_recording

_LOGGER = logging.getLogger(__name__)

DOMAIN = "cam_record"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the cam_record integration with camera-entity support."""
    store: Dict[str, Dict[str, Any]] = hass.data.setdefault(DOMAIN, {})

    async def handle_start(call: ServiceCall) -> None:
        camera_entity_id = call.data.get("camera_entity_id")
        stream_url = call.data.get("stream_url")
        filename = call.data.get("filename")

        if not filename:
            _LOGGER.error("cam_record.record_start: 'filename' is required")
            return

        url: str | None = None
        if camera_entity_id:
            url = await ha_camera.async_get_stream_source(hass, camera_entity_id)
            if not url:
                _LOGGER.error(
                    "cam_record.record_start: could not resolve stream for %s",
                    camera_entity_id,
                )
        if not url and stream_url:
            url = stream_url
        if not url:
            _LOGGER.error(
                "cam_record.record_start: provide either camera_entity_id or stream_url"
            )
            return

        if url in store:
            _LOGGER.warning("Recording already active for URL; ignoring start: %s", url)
            return

        process = await hass.async_add_executor_job(start_recording, url, filename)
        store[url] = {"process": process, "filename": filename}
        _LOGGER.info("Recording started: %s -> %s", url, filename)

    async def handle_stop(call: ServiceCall) -> None:
        camera_entity_id = call.data.get("camera_entity_id")
        stream_url = call.data.get("stream_url")

        url: str | None = None
        if camera_entity_id:
            url = await ha_camera.async_get_stream_source(hass, camera_entity_id)
        if not url and stream_url:
            url = stream_url
        if not url:
            _LOGGER.error(
                "cam_record.record_stop: provide either camera_entity_id or stream_url"
            )
            return

        entry = store.get(url)
        if not entry:
            _LOGGER.warning("No active recording for URL: %s", url)
            return

        await hass.async_add_executor_job(stop_recording, entry.get("process"))
        store.pop(url, None)
        _LOGGER.info("Recording stopped: %s", url)

    hass.services.async_register(DOMAIN, "record_start", handle_start)
    hass.services.async_register(DOMAIN, "record_stop", handle_stop)

    async def _on_ha_stop(event) -> None:
        # Try to gracefully stop all active ffmpeg processes on HA shutdown
        for url, data in list(store.items()):
            await hass.async_add_executor_job(stop_recording, data.get("process"))
        store.clear()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_ha_stop)
    return True
