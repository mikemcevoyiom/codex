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

After processing, a `conversion_status.json` file is saved to your
`~/Documents` folder. Each entry in this log includes the codec and file size
before and after processing:

```json
{
  "status": "converted",
  "input": "original.mkv",
  "output": "converted/original.mkv",
  "before_codec": "h264",
  "after_codec": "hevc",
  "before_size": 12345678,
  "after_size": 9876543
}
```

## Upload results to InfluxDB

You can push the `conversion_status.json` log into InfluxDB for reporting with Grafana.

1. Install the InfluxDB Python client:
   ```bash
   pip install influxdb-client
   ```
2. Export your connection details. The token can be stored in the `INFLUX_TOKEN` environment variable:
   ```bash
   export INFLUX_TOKEN=SC2OJktMgeOAQGjAxCx3NmNvq4_-CgEQoQiW7hST0TZiOt8q-zZA7MY-3X5VV3uJlB7DXbEnwCP7C95LhHAB1g==
   export INFLUX_URL=http://192.168.1.28:8086
   export INFLUX_ORG=my-org  # replace with your organization
   ```
3. Run the uploader script:
   ```bash
   python upload_to_influxdb.py
   ```

The script writes each entry to the `Video_Convert` bucket using the
`video_conversion` measurement. Once uploaded, add InfluxDB as a data source in
Grafana and build dashboards from that measurement.
