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

## Building a Windows executable

Bundle the app into `Video Updater.exe` with PyInstaller. The command below hides
the console window and includes the background image:

```powershell
pip install pyinstaller

pyinstaller --onefile --windowed --name "Video Updater" ^
  --add-data "images\movie_theatre.png;images" ^
  theatre_gui.py
```

The resulting executable will be placed in the `dist` directory.

## License

This project is licensed under the [MIT License](LICENSE).

## Versioning

The GUI displays its current version number in the window title. Increment the
version by editing the `VERSION` file and committing the change.
