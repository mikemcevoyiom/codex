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

## Theatre GUI

`theatre_gui.py` provides a very small Tkinter window that displays a movie
theatre background and an Exit button in the lower-right corner. To use it:

1. Download a movie theatre image you like and save it as
   `images/movie_theatre.png`.
2. Install the image dependency with `pip install Pillow`.
3. Run the script using `python3 theatre_gui.py`.

If the image file is missing, the script will raise an error with a helpful
message.

