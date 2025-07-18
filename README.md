# codex

This repository contains a small PyQt application for selecting audio and
subtitle streams in video files and optionally converting the video stream to
HEVC using FFmpeg. PyQt allows more customizable widgets, including styled
buttons.

By default the script opens a directory located at `videos/unprocessed/new`
within your home folder. You can specify a different location by setting the
`STREAM_SELECTOR_DIR` environment variable before running the application.

After launching the script, choose a folder containing your videos. Two buttons
are available and each operation will be applied to every video in the selected
folder:

* **Convert to HEVC** – converts the currently selected file to HEVC if it is not
  already encoded in HEVC or AV1.
* **Update Streams** – remuxes the chosen audio and subtitle streams while
  keeping the video stream as is.

After processing, two log files are written to your `~/Documents` folder:

- `convert.json` – details of any HEVC conversions
- `streams.json` – summaries of selected audio and subtitle streams

## Upload results to InfluxDB

When you exit the application, the logs are automatically uploaded to InfluxDB
using `upload_to_influxdb.py`. You can also run this script manually if
needed. It reads `convert.json` and `streams.json` and writes each entry using
the filename stem as the measurement name. The script verifies connectivity
to InfluxDB via `client.ping()` before attempting an upload, and each record's
`time` field is used as the timestamp if present.

1. Install the InfluxDB Python client:
   ```bash
   pip install influxdb-client
   ```
2. Export your connection details. The token can be stored in the `INFLUX_TOKEN` environment variable:
   ```bash
   export INFLUX_TOKEN=SC2OJktMgeOAQGjAxCx3NmNvq4_-CgEQoQiW7hST0TZiOt8q-zZA7MY-3X5VV3uJlB7DXbEnwCP7C95LhHAB1g==
   export INFLUX_HOST=http://192.168.1.28:8086
 export INFLUX_ORG=my-org  # replace with your organization
  ```
3. Run the uploader script manually, or simply exit the application to trigger
   an automatic upload:
  ```bash
  python upload_to_influxdb.py
  ```

Each log is written to the `Video_Convert` bucket with a measurement name
matching the JSON filename (for example `convert` or `streams`). Once uploaded,
add InfluxDB as a data source in Grafana and build dashboards from those
measurements.
