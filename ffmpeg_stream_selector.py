from pathlib import Path
import os
import sys
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
)
from PyQt5.QtCore import Qt
import subprocess
import json


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
        layout.addWidget(self.bitrate_dropdown, 3, 1)

        self.verify_check = QCheckBox("Verify stream order after conversion")
        self.verify_check.setChecked(True)
        layout.addWidget(self.verify_check, 5, 0, 1, 2)

        self.convert_video_btn = QPushButton("Convert to HEVC")
        self.convert_video_btn.setStyleSheet("background-color: #add8e6;")
        self.convert_video_btn.clicked.connect(self.convert_to_hevc)
        layout.addWidget(self.convert_video_btn, 4, 0)

        self.update_streams_btn = QPushButton("Update Streams")
        self.update_streams_btn.setStyleSheet("background-color: #90ee90;")
        self.update_streams_btn.clicked.connect(self.update_streams)
        layout.addWidget(self.update_streams_btn, 4, 1)

        # Track processed directories for cleanup after exiting
        self.processed_dirs = set()

        # Collect status information for JSON output
        self.status_log = []

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.quit_app)
        layout.addWidget(self.exit_btn, 6, 0, 1, 2)

    def log_status(self, status, input_file=None, output_file=None, message=""):
        entry = {
            "status": status,
            "input": input_file,
            "output": output_file,
            "message": message,
        }
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
        """Write collected status information to a JSON file."""
        output_dir = Path(r"D:\Video\unprocessed\new")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "conversion_status.json", "w", encoding="utf-8") as f:
            json.dump(self.status_log, f, indent=2)

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
            self, "Select folder with video files"
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
            return

        self.current_index = 0
        self.selected_file = self.video_files[self.current_index]
        self.current_file = self.selected_file
        self.populate_stream_dropdowns(self.selected_file)

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
            return

        for input_file in self.video_files:
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
                subprocess.run(cmd, check=True)
                self.processed_dirs.add(converted_dir)
                self.current_file = output_path
                self.log_status(
                    "converted",
                    input_file=input_file,
                    output_file=output_path,
                )
            except subprocess.CalledProcessError as e:
                print("FFmpeg error:", e)
                self.log_status(
                    "error",
                    input_file=input_file,
                    message="FFmpeg failed during conversion",
                )

        self.ask_commit_updates()

    def update_streams(self):
        if not getattr(self, "video_files", None):
            self.log_status("error", message="Please select a folder first.")
            return

        audio = self.audio_dropdown.currentText()
        subtitle = self.subtitle_dropdown.currentText()
        if not audio or not subtitle:
            self.log_status(
                "error", message="Please select both audio and subtitle streams."
            )
            return

        subtitle_index = subtitle.split(" ")[1]
        audio_index = audio.split(" ")[1]

        for input_file in self.video_files:
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
                subprocess.run(cmd, check=True)
                self.processed_dirs.add(converted_dir)
                self.current_file = output_path
                self.log_status(
                    "streams_updated",
                    input_file=input_file,
                    output_file=output_path,
                )
            except subprocess.CalledProcessError as e:
                print("FFmpeg error:", e)
                self.log_status(
                    "error",
                    input_file=input_file,
                    message="FFmpeg failed during stream update",
                )

        self.ask_commit_updates()

    def verify_stream_order(self, first_converted_file):
        import subprocess, json

        try:
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-select_streams",
                "v:a:s",
                "-of",
                "json",
                first_converted_file,
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            data = json.loads(result.stdout)
            expected_order = ["video", "audio", "subtitle"]
            actual_order = {
                s["index"]: s["codec_type"] for s in data.get("streams", [])
            }
            for idx, expected_type in enumerate(expected_order):
                if actual_order.get(idx) != expected_type:
                    return False
            return True
        except Exception as e:
            print(f"Verification error: {e}")
            return False


if __name__ == "__main__":
    qt_app = QApplication(sys.argv)
    window = StreamSelectorApp()
    window.show()
    qt_app.exec_()

    # Handle any remaining processed files when the window is closed directly
    if getattr(window, "processed_dirs", None):
        window.commit_converted_files()
        window.write_status_log()
