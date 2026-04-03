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

### Ubuntu/Debian note (PEP 668: externally-managed-environment)

If you see `error: externally-managed-environment`, you are using the system
Python `pip` instead of a project virtual environment `pip`. On Ubuntu/Debian,
use the steps below to ensure the venv-local installer is used:

```bash
# one-time system packages
sudo apt update
sudo apt install -y python3-venv python3-full

# from the project root
python3 -m venv .venv
source .venv/bin/activate

# always prefer python -m pip to avoid pip-path confusion
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Quick verification:

```bash
which python
which pip
python -m pip --version
```

`which python` and `which pip` should both point inside `.venv/`.

## InfluxDB Configuration

`theatre_gui.py` reads optional environment variables to configure InfluxDB:

| Variable | Default |
|----------|---------|
| `INFLUXDB_URL` | `http://192.168.1.28:8086/` |
| `INFLUXDB_TOKEN` | `vYAzRtDOejTeACp1SJne6TIPHzamWcpvi_Ekd3R2VA1Zvr4zFSa-bmiWzsy1DQuIBwfQ8psG-CUP7HOqSRgCWg==` |
| `INFLUXDB_ORG` | `Waterfall` |
| `INFLUXDB_BUCKET` | `Video_Update` |

Override these values by setting the environment variables before launching the
application.

## Building a Windows executable

Bundle the app into `Video Updater.exe` with PyInstaller. The command below hides
the console window and includes the background image:

```powershell
pip install pyinstaller

cd C:\Users\Mike\Documents\Python\
pyinstaller --onefile --windowed --name "Video Updater" `
  --add-data "Y:\Code\Python\codex\images\movie_theatre.png;images" `
  Y:\Code\Python\codex\theatre_gui.py

Copy-Item ".\dist\Video Updater.exe" "Y:\Code\Python\codex\"
```

The final `Copy-Item` command moves the generated executable back into the
project directory.

## Building a Linux executable (Ubuntu)

If you moved from Windows to Ubuntu and want a standalone binary, use
PyInstaller on Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller

# install runtime tools used by theatre_gui.py
sudo apt update
sudo apt install -y ffmpeg python3-tk

pyinstaller --onefile --windowed --name "video-updater" \
  --add-data "images/movie_theatre.png:images" \
  theatre_gui.py

./dist/video-updater
```

Notes:
- On Linux, `--add-data` uses `source:dest` (colon).
- The generated binary is Linux-native and will not run on Windows.

## License

This project is licensed under the [MIT License](LICENSE).

## Versioning

The GUI displays its current version number in the window title. Increment the
version by editing the `VERSION` file and committing the change.
