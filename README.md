# codex

This repository contains utilities for managing video processing and logging with Python and PowerShell.
It includes a PyQt application for selecting audio and subtitle streams, scripts for working with InfluxDB, and a small Tkinter demo GUI.

## ffmpeg_stream_selector.py

`ffmpeg_stream_selector.py` provides a graphical interface to choose audio and subtitle streams from a folder of video files. It can also convert the video stream to HEVC using FFmpeg.

The application opens a default folder at `videos/unprocessed/new` under your home directory. Set the `STREAM_SELECTOR_DIR` environment variable to use a different folder. The last selected folder is remembered between runs.

Two actions are available:

* **Convert to HEVC** – converts files to HEVC when they are not already encoded in HEVC or AV1.
* **Update Streams** – remuxes the selected audio and subtitle streams while keeping the original video stream.

Processing results are written to your `~/Documents` folder as `convert.json` and `streams.json`.

## theatre_gui.py

A minimal Tkinter window displaying a movie theatre background with an Exit button. Launch it with:

```bash
python theatre_gui.py
```

Ensure a graphical environment is available since Tkinter requires an active display server.

## upload_to_influxdb.py

Reads the JSON log files created by `ffmpeg_stream_selector.py` and uploads the entries to an InfluxDB bucket specified by the environment variables `INFLUX_HOST`, `INFLUX_ORG`, and `INFLUX_TOKEN`.

Run with:

```bash
python upload_to_influxdb.py
```

## PowerShell Scripts

* `Check-InfluxBucketEmpty.ps1` – checks whether the target InfluxDB bucket contains any data.
* `Wipe-InfluxBucket.ps1` – deletes all data from the specified bucket while leaving the bucket itself intact.

Both scripts prompt for an API token if `INFLUX_TOKEN` is not set.

## Requirements

See [`requirements.txt`](requirements.txt) for the Python dependencies (Pillow, PyQt5, and influxdb-client).

## License

This project is licensed under the [MIT License](LICENSE).
