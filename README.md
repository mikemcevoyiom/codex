# codex

This repository contains a small Tkinter application for selecting audio and
subtitle streams in video files and optionally converting the video stream to
HEVC using FFmpeg.

After launching the script, choose a folder containing your videos. Two buttons
are available and each operation will be applied to every video in the selected
folder:

* **Convert to HEVC** – converts the currently selected file to HEVC if it is not
  already encoded in HEVC or AV1.
* **Update Streams** – remuxes the chosen audio and subtitle streams while
  keeping the video stream as is.
