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
