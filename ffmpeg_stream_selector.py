from pathlib import Path
import os
import sys

# Default directory used when no folder is selected. Users can override
# this path with the STREAM_SELECTOR_DIR environment variable. The default
# falls back to a "videos/unprocessed/new" directory in the user's home
# folder to work across operating systems.
DEFAULT_VIDEO_DIR = Path(
    os.getenv("STREAM_SELECTOR_DIR", Path.home() / "videos" / "unprocessed" / "new")
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QProgressBar,
)
from PyQt5.QtCore import Qt
import subprocess
import json
from datetime import datetime


class StreamSelectorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFmpeg Stream Selector")
        # Increase window size by one third to provide more room for widgets
        self.resize(600, 400)

        layout = QGridLayout()
        self.setLayout(layout)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.select_file_btn = QPushButton("Select Folder")
        self.select_file_btn.clicked.connect(self.select_path)
        # The button will also display the chosen folder path
        self.select_file_btn.setMinimumHeight(50)
        layout.addWidget(self.select_file_btn, 0, 0, 1, 2)

        self.audio_label = QLabel("Select Audio Stream:")
        layout.addWidget(self.audio_label, 1, 0)
        self.audio_dropdown = QComboBox()
        layout.addWidget(self.audio_dropdown, 1, 1)

        self.subtitle_label = QLabel("Select Subtitle Stream:")
        layout.addWidget(self.subtitle_label, 2, 0)
        self.subtitle_dropdown = QComboBox()
        layout.addWidget(self.subtitle_dropdown, 2, 1)

        self.bitrate_label = QLabel("Bitrate (kbps):")
        layout.addWidget(self.bitrate_label, 3, 0)
        self.bitrate_dropdown = QComboBox()
        self.bitrate_dropdown.addItems([str(b) for b in range(1000, 4500, 500)])
        self.bitrate_dropdown.setCurrentText("2000")
        layout.addWidget(self.bitrate_dropdown, 3, 1)

        self.update_streams_btn = QPushButton("Update Streams")
        self.update_streams_btn.setStyleSheet("background-color: #90ee90;")
        self.update_streams_btn.clicked.connect(self.update_streams)
        layout.addWidget(self.update_streams_btn, 4, 0, 1, 2)
        self.update_streams_btn.setEnabled(False)

        self.convert_video_btn = QPushButton("Convert to HEVC")
        self.convert_video_btn.setStyleSheet("background-color: #add8e6;")
        self.convert_video_btn.clicked.connect(self.convert_to_hevc)
        layout.addWidget(self.convert_video_btn, 5, 0, 1, 2)
        self.convert_video_btn.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar, 6, 0, 1, 2)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label, 7, 0, 1, 2)

        # Track processed directories for cleanup after exiting
        self.processed_dirs = set()

        # Collect status information for JSON output
        self.status_log = []
        # Separate logs for conversion and stream updates
        self.convert_log = []
        self.streams_log = []

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.quit_app)
        layout.addWidget(self.exit_btn, 8, 0, 1, 2)

    def log_status(
        self,
        status,
        input_file=None,
        output_file=None,
        message="",
        before_codec=None,
        after_codec=None,
        before_size=None,
        after_size=None,
    ):
        entry = {
            "status": status,
            "input": input_file,
            "output": output_file,
            "message": message,
        }
        if before_codec is not None:
            entry["before_codec"] = before_codec
        if after_codec is not None:
            entry["after_codec"] = after_codec
        if before_size is not None:
            entry["before_size"] = before_size
        if after_size is not None:
            entry["after_size"] = after_size
        self.status_log.append(entry)
        print(f"{status.upper()}: {message or output_file or input_file}")

    def commit_converted_files(self):
        """Move processed files back to their original location and clean up."""
        import shutil

        for conv_dir in list(self.processed_dirs):
            if not os.path.isdir(conv_dir):
                continue
            for file in os.listdir(conv_dir):
                src_path = os.path.join(conv_dir, file)
                dst_path = os.path.join(os.path.dirname(conv_dir), file)
                shutil.move(src_path, dst_path)
            try:
                os.rmdir(conv_dir)
            except OSError:
                print(f"Could not remove {conv_dir} — it may not be empty.")
        self.processed_dirs.clear()

    def write_status_log(self):
        """Write collected status information to a JSON file in ~/Documents."""
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        with open(documents_dir / "conversion_status.json", "w", encoding="utf-8") as f:
            json.dump(self.status_log, f, indent=2)

    def write_convert_log(self):
        """Write convert_to_hevc results to ~/Documents/convert.json."""
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        with open(documents_dir / "convert.json", "w", encoding="utf-8") as f:
            json.dump(self.convert_log, f, indent=2)

    def write_streams_log(self):
        """Write update_streams results to ~/Documents/streams.json."""
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        with open(documents_dir / "streams.json", "w", encoding="utf-8") as f:
            json.dump(self.streams_log, f, indent=2)

    def ask_commit_updates(self):
        """Prompt the user to commit processed files if any exist."""
        if not self.processed_dirs:
            return
        reply = QMessageBox.question(
            self,
            "Processing Complete",
            "All work completed. Commit updates to original files?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.commit_converted_files()
            self.write_status_log()
            try:
                import upload_to_influxdb

                upload_to_influxdb.main()
            except Exception as e:
                print(f"Influx upload failed: {e}")
            QMessageBox.information(
                self,
                "Commit Complete",
                "Converted files have been moved back.",
            )

    def quit_app(self):
        """Handle exit button click."""
        self.ask_commit_updates()
        QApplication.quit()

    def select_path(self):
        from pathlib import Path

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select folder with video files",
            str(DEFAULT_VIDEO_DIR),
        )
        if not folder:
            return

        self.selected_folder = folder
        # Show the selected folder on the button itself
        self.select_file_btn.setText(f"Select Folder\n{folder}")
        self.select_file_btn.setToolTip(folder)

        self.video_files = sorted(
            [str(f) for f in Path(folder).rglob("*.mkv")]
            + [str(f) for f in Path(folder).rglob("*.mp4")]
        )
        if not self.video_files:
            self.log_status(
                "error", message="No MKV or MP4 files found in selected folder."
            )
            self.convert_video_btn.setEnabled(False)
            self.update_streams_btn.setEnabled(False)
            return

        self.current_index = 0
        self.selected_file = self.video_files[self.current_index]
        self.current_file = self.selected_file
        self.populate_stream_dropdowns(self.selected_file)
        self.convert_video_btn.setEnabled(True)
        self.update_streams_btn.setEnabled(True)

    def run_ffprobe(self, filepath, stream_type):
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    stream_type,
                    "-show_entries",
                    "stream=index,codec_type:stream_tags=language,title",
                    "-of",
                    "json",
                    filepath,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout).get("streams", [])
        except subprocess.CalledProcessError as e:
            print(f"ffprobe failed for stream type '{stream_type}':", e)
            return []

    def parse_ffmpeg_progress(self, line):
        fps = None
        time_pos = None
        if "fps=" in line or "time=" in line:
            parts = line.strip().split()
            for part in parts:
                if part.startswith("fps="):
                    fps = part.split("=", 1)[1]
                elif part.startswith("time="):
                    time_pos = part.split("=", 1)[1]
        return fps, time_pos

    def get_video_codec(self, filepath):
        """Return the codec name of the first video stream."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=codec_name",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    filepath,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return result.stdout.strip().lower()
        except Exception:
            return None

    def get_duration(self, filepath):
        """Return the duration of the input file in seconds."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    filepath,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"ffprobe duration error for {filepath}:", e)
            return None

    def time_to_seconds(self, time_str):
        """Convert an HH:MM:SS.xxx time string to seconds."""
        try:
            h, m, s = time_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            return None

    def populate_stream_dropdowns(self, filepath):
        audio_streams = self.run_ffprobe(filepath, "a")
        subtitle_streams = self.run_ffprobe(filepath, "s")

        audio_options = []
        subtitle_options = []
        default_audio = None
        default_subtitle = None

        for stream in audio_streams:
            index = stream.get("index")
            lang = stream.get("tags", {}).get("language", "und")
            title = stream.get("tags", {}).get("title", "")
            label = f"Stream {index} - {lang}"
            if "forced" in title.lower():
                label += " [FORCED]"
            if title:
                label += f" ({title})"
            audio_options.append(label)

            if default_audio is None and lang.lower() == "eng":
                default_audio = label

        for stream in subtitle_streams:
            index = stream.get("index")
            lang = stream.get("tags", {}).get("language", "und")
            title = stream.get("tags", {}).get("title", "")
            label = f"Stream {index} - {lang}"
            if "forced" in title.lower():
                label += " [FORCED]"
            if title:
                label += f" ({title})"
            subtitle_options.append(label)

            title_lower = title.lower()
            if (
                default_subtitle is None
                and lang.lower() == "eng"
                and ("signs" in title_lower or "forced" in title_lower)
            ):
                default_subtitle = label

        self.audio_dropdown.clear()
        self.audio_dropdown.addItems(audio_options)
        if default_audio and default_audio in audio_options:
            self.audio_dropdown.setCurrentIndex(audio_options.index(default_audio))

        self.subtitle_dropdown.clear()
        self.subtitle_dropdown.addItems(subtitle_options)
        if default_subtitle and default_subtitle in subtitle_options:
            self.subtitle_dropdown.setCurrentIndex(
                subtitle_options.index(default_subtitle)
            )

    def convert_to_hevc(self):
        if not getattr(self, "video_files", None):
            self.log_status("error", message="Please select a folder first.")
            QMessageBox.warning(
                self,
                "No Folder Selected",
                "Please select a folder first.",
            )
            return

        self.status_label.setText("Converting... please wait")
        self.progress_bar.setRange(0, len(self.video_files) * 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.convert_video_btn.setEnabled(False)
        self.update_streams_btn.setEnabled(False)
        QApplication.processEvents()

        # reset convert log for this run
        self.convert_log = []

        for idx, input_file in enumerate(self.video_files, start=1):
            duration = self.get_duration(input_file)
            before_size = os.path.getsize(input_file)
            try:
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-select_streams",
                        "v:0",
                        "-show_entries",
                        "stream=codec_name",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        input_file,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                codec = result.stdout.strip().lower()
                if codec in ("hevc", "av1"):
                    self.log_status(
                        "skipped",
                        input_file=input_file,
                        message=f"Already {codec.upper()}",
                        before_codec=codec,
                        after_codec=codec,
                        before_size=os.path.getsize(input_file),
                        after_size=os.path.getsize(input_file),
                    )
                    self.convert_log.append(
                        {
                            "time": datetime.now().isoformat(),
                            "filename": os.path.basename(input_file),
                            "before_size": before_size,
                            "after_size": before_size,
                            "before_codec": codec,
                            "after_codec": codec,
                        }
                    )
                    continue
            except Exception as e:
                self.log_status(
                    "error", input_file=input_file, message=f"Codec check failed: {e}"
                )
                continue

            converted_dir = os.path.join(os.path.dirname(input_file), "converted")
            os.makedirs(converted_dir, exist_ok=True)
            output_path = os.path.join(converted_dir, os.path.basename(input_file))

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_file,
                "-c:v",
                "hevc_amf",
                "-c:a",
                "copy",
                "-c:s",
                "copy",
                "-map_chapters",
                "0",
                "-usage",
                "transcoding",
                "-b:v",
                self.bitrate_dropdown.currentText() + "k",
                output_path,
            ]

            try:
                process = subprocess.Popen(
                    cmd, stderr=subprocess.PIPE, text=True
                )
                for line in process.stderr:
                    fps, time_pos = self.parse_ffmpeg_progress(line)
                    if fps or time_pos:
                        self.status_label.setText(
                            f"fps: {fps} time: {time_pos}"
                        )
                        if duration and time_pos:
                            secs = self.time_to_seconds(time_pos)
                            if secs is not None:
                                progress = min(secs / duration, 1.0)
                                self.progress_bar.setValue(
                                    int((idx - 1 + progress) * 100)
                                )
                        QApplication.processEvents()
                ret = process.wait()
                if ret == 0:
                    self.processed_dirs.add(converted_dir)
                    self.current_file = output_path
                    self.log_status(
                        "converted",
                        input_file=input_file,
                        output_file=output_path,
                        before_codec=codec,
                        after_codec=self.get_video_codec(output_path),
                        before_size=before_size,
                        after_size=os.path.getsize(output_path),
                    )
                    self.convert_log.append(
                        {
                            "time": datetime.now().isoformat(),
                            "filename": os.path.basename(input_file),
                            "before_size": before_size,
                            "after_size": os.path.getsize(output_path),
                            "before_codec": codec,
                            "after_codec": self.get_video_codec(output_path),
                        }
                    )
                else:
                    raise subprocess.CalledProcessError(ret, cmd)
            except subprocess.CalledProcessError as e:
                print("FFmpeg error:", e)
                self.log_status(
                    "error",
                    input_file=input_file,
                    message="FFmpeg failed during conversion",
                )

            self.progress_bar.setValue(idx * 100)
            QApplication.processEvents()

        self.ask_commit_updates()
        self.write_convert_log()
        self.status_label.setText("Done")
        self.progress_bar.hide()
        self.convert_video_btn.setEnabled(True)
        self.update_streams_btn.setEnabled(True)

    def update_streams(self):
        if not getattr(self, "video_files", None):
            self.log_status("error", message="Please select a folder first.")
            QMessageBox.warning(
                self,
                "No Folder Selected",
                "Please select a folder first.",
            )
            return

        self.status_label.setText("Updating streams... please wait")
        self.progress_bar.setRange(0, len(self.video_files) * 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.convert_video_btn.setEnabled(False)
        self.update_streams_btn.setEnabled(False)
        QApplication.processEvents()

        # reset streams log for this run
        self.streams_log = []

        audio = self.audio_dropdown.currentText()
        subtitle = self.subtitle_dropdown.currentText()
        if not audio or not subtitle:
            self.log_status(
                "error", message="Please select both audio and subtitle streams."
            )
            return

        subtitle_index = subtitle.split(" ")[1]
        audio_index = audio.split(" ")[1]

        for idx, input_file in enumerate(self.video_files, start=1):
            duration = self.get_duration(input_file)
            before_codec = self.get_video_codec(input_file)
            before_size = os.path.getsize(input_file)
            converted_dir = os.path.join(os.path.dirname(input_file), "converted")
            os.makedirs(converted_dir, exist_ok=True)
            output_path = os.path.join(converted_dir, os.path.basename(input_file))

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                input_file,
                "-map",
                "0:v:0",
                "-map",
                f"0:{audio_index}",
                "-map",
                f"0:{subtitle_index}",
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-c:s",
                "copy",
                "-map_chapters",
                "0",
                "-disposition:s:0",
                "forced",
                output_path,
            ]

            try:
                process = subprocess.Popen(
                    cmd, stderr=subprocess.PIPE, text=True
                )
                for line in process.stderr:
                    fps, time_pos = self.parse_ffmpeg_progress(line)
                    if fps or time_pos:
                        self.status_label.setText(
                            f"fps: {fps} time: {time_pos}"
                        )
                        if duration and time_pos:
                            secs = self.time_to_seconds(time_pos)
                            if secs is not None:
                                progress = min(secs / duration, 1.0)
                                self.progress_bar.setValue(
                                    int((idx - 1 + progress) * 100)
                                )
                        QApplication.processEvents()
                ret = process.wait()
                if ret == 0:
                    self.processed_dirs.add(converted_dir)
                    self.current_file = output_path
                    self.log_status(
                        "streams_updated",
                        input_file=input_file,
                        output_file=output_path,
                        before_codec=before_codec,
                        after_codec=self.get_video_codec(output_path),
                        before_size=before_size,
                        after_size=os.path.getsize(output_path),
                    )
                    self.streams_log.append(
                        {
                            "time": datetime.now().isoformat(),
                            "filename": os.path.basename(input_file),
                            "audio_stream": audio,
                            "subtitle_stream": subtitle,
                        }
                    )
                else:
                    raise subprocess.CalledProcessError(ret, cmd)
            except subprocess.CalledProcessError as e:
                print("FFmpeg error:", e)
                self.log_status(
                    "error",
                    input_file=input_file,
                    message="FFmpeg failed during stream update",
                )

            self.progress_bar.setValue(idx * 100)
            QApplication.processEvents()

        self.ask_commit_updates()
        self.write_streams_log()
        self.status_label.setText("Done")
        self.progress_bar.hide()
        self.convert_video_btn.setEnabled(True)
        self.update_streams_btn.setEnabled(True)


if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    window = StreamSelectorApp()
    window.show()
    qt_app.exec_()

    # Handle any remaining processed files when the window is closed directly
    if getattr(window, "processed_dirs", None):
        window.commit_converted_files()
        window.write_status_log()
        window.write_convert_log()
        window.write_streams_log()
        try:
            import upload_to_influxdb

            upload_to_influxdb.main()
        except Exception as e:
            print(f"Influx upload failed: {e}")
