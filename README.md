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
