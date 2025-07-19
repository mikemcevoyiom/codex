# codex

This repository contains a small PyQt application for selecting audio and
subtitle streams in video files and optionally converting the video stream to
HEVC using FFmpeg. PyQt allows more customizable widgets, including styled
buttons.

By default the script opens a directory located at `videos/unprocessed/new`
within your home folder. You can specify a different location by setting the
`STREAM_SELECTOR_DIR` environment variable before running the application.
The application also remembers the last folder you used and defaults to that
location the next time it runs.

After launching the script, choose a folder containing your videos. Two
image-based buttons appear with the same green and blue backgrounds as before,
loading their icons from the `images` directory. Click these pictures to
perform the following actions on every video in the selected folder:

* **Convert to HEVC** – converts the currently selected file to HEVC if it is not
  already encoded in HEVC or AV1.
* **Update Streams** – remuxes the chosen audio and subtitle streams while
  keeping the video stream as is.

After processing, two log files are written to your `~/Documents` folder:

- `convert.json` – details of any HEVC conversions
- `streams.json` – summaries of selected audio and subtitle streams

