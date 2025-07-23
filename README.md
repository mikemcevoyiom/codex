# codex

This repository now focuses on a single Tkinter example. The program provides a
small GUI for processing video files with FFmpeg. You can pick a folder of MKV
or MP4 files, choose which audio and subtitle tracks to keep, and optionally
convert the videos to the HEVC codec. All operations run through a simple
Tkinter window.

## theatre_gui.py

`theatre_gui.py` displays a movie theatre background and provides controls to
choose a folder, update streams, convert videos, and exit the app. Launch it with:

```bash
python theatre_gui.py
```

The script expects `images/movie_theatre.png` to be present and requires a graphical environment.

## Requirements

Only [Pillow](https://python-pillow.org/) is required. Install dependencies using:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the [MIT License](LICENSE).
