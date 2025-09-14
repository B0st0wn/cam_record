# Cam Record — On‑Demand RTSP Recording for Home Assistant

Record any RTSP (or other `ffmpeg`‑readable) camera stream to a local file **on demand** from Home Assistant. Start when motion begins, keep recording as long as you want, and stop when motion clears — or just tap a dashboard button to toggle recording.

> **Privacy:** All example addresses and paths below use placeholders like `<CAMERA_HOST>`, `<PORT>`, and `<STREAM_PATH>`. Replace them with your actual values.

> **Why?** Home Assistant’s built‑in `camera.record` makes fixed‑length clips. **Cam Record** lets you **start/stop freely**, so your clip can be minutes or hours — limited mainly by storage.

---

## Features

* **Two services** to control a background `ffmpeg` process:

  * `cam_record.record_start(camera_entity_id | stream_url, filename)`
  * `cam_record.record_stop(camera_entity_id | stream_url)`
* **Use camera entities directly**: Provide `camera_entity_id` and the integration resolves the stream URL (fallback to `stream_url` supported).
* **Graceful stop**: Recordings finalize cleanly for MP4 playback.
* **Works with RTSP** (and anything `ffmpeg` can read).
* **Saves anywhere you choose** (e.g., under `/media/` so clips appear in HA’s Media browser).
* **Designed for automations** (motion start/stop, doorbell press) and **dashboard toggles**.

> Tip: If your camera is quirky, run it through **go2rtc** and use a stable RTSP/MP4‑friendly URL.

---

## Requirements

* Home Assistant (recent version)
* `ffmpeg` available in the HA environment (included in HA OS/Container)
* A **writable** output directory (create it first). Recommended: a subfolder under `/media/`.

---

## Installation

### Option A — HACS (Custom Repository)

1. HACS → Integrations → ⋯ → **Custom repositories** → add `https://github.com/B0st0wn/cam_record` (Category: *Integration*).
2. Install **Cam Record**.
3. **Restart Home Assistant**.

### Option B — Manual

1. Copy the folder to your HA config:

   ```
   <config>/custom_components/cam_record/
   ```
2. **Restart Home Assistant**.

The services will appear automatically in **Developer Tools → Services**.

---

## Configuration

Add these lines to your **configuration.yaml** and restart Home Assistant:

```yaml
ffmpeg:
cam_record:
```

## Services

### `cam_record.record_start`

Starts an `ffmpeg` process and writes the stream to the provided path.

**Fields**

* `camera_entity_id` (string, optional): Camera entity to record (e.g., `camera.front_door`). Preferred.
* `stream_url` (string, optional): RTSP/HTTP/etc. Used if no camera entity is provided.
* `filename` (string, required): Full output path (e.g., `/media/front_door/2025-08-17_11-45-00.mp4`).

At least one of `camera_entity_id` or `stream_url` is required.

**Examples**

By camera entity (preferred):

```yaml
service: cam_record.record_start
data:
  camera_entity_id: camera.front_door
  filename: /media/front_door/front_door_{{ now().strftime('%Y-%m-%d_%H-%M-%S') }}.mp4
```

By raw stream URL (advanced):

```yaml
service: cam_record.record_start
data:\n      camera_entity_id: camera.front_door\n      filename: /media/front_door/front_door_{{ now().strftime('%Y-%m-%d_%H-%M-%S') }}.mp4
```

### `cam_record.record_stop`

Stops an active recording.

**Fields**

* `camera_entity_id` (string, optional): Camera entity to stop.
* `stream_url` (string, optional): URL to stop (if you started by URL).

Provide the same identifier type you used for start. If both are provided, the camera entity is used.

**Examples**

By camera entity:

```yaml
service: cam_record.record_stop
data:
  camera_entity_id: camera.front_door
```

By stream URL:

```yaml
service: cam_record.record_stop
data:
      camera_entity_id: camera.front_door
```

---

## Quick Start (2 minutes)

1. Create a directory for recordings, e.g. `/media/front_door`.
2. From Developer Tools → Services, call `cam_record.record_start` with your camera entity and a filename under that folder.
3. When you’re done, call `cam_record.record_stop` with the **same** camera entity.

---

## Example Automations

### A) Record while motion is ON; stop when it’s OFF

```yaml
alias: Front Door - Record while motion
mode: restart

trigger:
  - platform: state
    entity_id: binary_sensor.front_door_motion
    to: "on"
  - platform: state
    entity_id: binary_sensor.front_door_motion
    to: "off"
    for: "00:00:10"   # optional grace period to avoid rapid stop/start

variables:
      camera_entity_id: camera.front_door
  outdir: /media/front_door

action:
  - choose:
      - conditions: "{{ trigger.to_state.state == 'on' }}"
        sequence:
          - service: cam_record.record_start
            data:
              camera_entity_id: "{{ cam }}"
              filename: "{{ outdir }}/front_door_{{ now().strftime('%Y-%m-%d_%H-%M-%S') }}.mp4"
      - conditions: "{{ trigger.to_state.state == 'off' }}"
        sequence:
          - service: cam_record.record_stop
            data:
              camera_entity_id: "{{ cam }}"
```

### B) Dashboard toggle button to Start/Stop

Create a helper and two tiny automations that react to it.

**Helper**

```yaml
input_boolean:
  front_door_recording:
    name: Front Door Recording
```

**Automation: ON → start recording**

```yaml
alias: Front Door Recording - Start
trigger:
  - platform: state
    entity_id: input_boolean.front_door_recording
    to: "on"
action:
  - service: cam_record.record_start
    data:
      camera_entity_id: camera.front_door
      filename: /media/front_door/front_door_{{ now().strftime('%Y-%m-%d_%H-%M-%S') }}.mp4
mode: single
```

**Automation: OFF → stop recording**

```yaml
alias: Front Door Recording - Stop
trigger:
  - platform: state
    entity_id: input_boolean.front_door_recording
    to: "off"
action:
  - service: cam_record.record_stop
    data:
      camera_entity_id: camera.front_door
mode: single
```

**Lovelace (example button)**

```yaml
type: button
entity: input_boolean.front_door_recording
name: Record Front Door
icon: mdi:record-circle
show_state: true
```

---

## Troubleshooting

* **No file appears** → Ensure the parent folder exists and is writable (try under `/media`).
* **Cannot stop recording**  Use the same identifier type you used to start (entity vs URL). If you started by entity, stop by entity.
* **RTSP instability** → Prefer TCP RTSP URLs (many cameras accept `?mp4`/TCP variants) or normalize via go2rtc.
* **Storage growth** → Long clips grow quickly; use dated filenames/folders and prune periodically.

---

## Development

* **Domain:** `cam_record`
* **Structure:** `custom_components/cam_record/`

  * `__init__.py` - async services, camera-entity support, tracks processes
  * `services.yaml` — schemas and field hints
  * `manifest.json` — integration metadata
  * `recorder.py` - thin wrapper around `ffmpeg` execution (graceful stop supported)

Contributions welcome!







