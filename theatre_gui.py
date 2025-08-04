import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk


# Default directory used when no folder is selected. Users can override
# this path with the STREAM_SELECTOR_DIR environment variable. The default
# falls back to a "videos/unprocessed/new" directory in the user's home
# folder to work across operating systems.
DEFAULT_VIDEO_DIR = Path(
    os.getenv("STREAM_SELECTOR_DIR", Path.home() / "videos" / "unprocessed" / "new")
)

# Store GUI settings (currently just the last selected folder)
SETTINGS_FILE = Path.home() / ".theatre_gui_settings.json"

# Flag to prevent opening a console window for subprocesses on Windows.
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

class TheatreApp(tk.Tk):
    """Simple window displaying a movie theatre background with an exit button."""

    def __init__(self, image_path: Path):
        super().__init__()
        self.title("Movie Theatre")
        self.resizable(False, False)
        # Fixed window size
        self.geometry("800x800")

        if not image_path.exists():
            raise FileNotFoundError(
                f"Background image missing: {image_path}\n"
                "Download or provide your own image named 'movie_theatre.png'"
            )

        img = Image.open(image_path).resize((800, 800))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas = tk.Canvas(self, width=800, height=800, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")

        # widgets are placed directly on the canvas so the background image shows
        # Shift all widgets upward for a more centered layout
        y_pos = 120

        # Select folder button - label will also display the chosen folder
        self.select_file_btn = tk.Button(
            self, text="Select Folder", command=self.select_path, width=30, height=2
        )
        self.canvas.create_window(400, y_pos, window=self.select_file_btn, anchor="n")
        y_pos += 60

        last_folder = self._load_last_folder()
        if last_folder:
            self.select_file_btn.config(text=f"Select Folder\n{last_folder}")
            self.select_file_btn.tooltip = last_folder

        audio_label = tk.Label(self, text="Select Audio Stream:")
        self.canvas.create_window(300, y_pos, window=audio_label, anchor="e")
        self.audio_dropdown = ttk.Combobox(self, state="readonly", width=40)
        self.canvas.create_window(310, y_pos, window=self.audio_dropdown, anchor="w")
        y_pos += 30

        subtitle_label = tk.Label(self, text="Select Subtitle Stream:")
        self.canvas.create_window(300, y_pos, window=subtitle_label, anchor="e")
        self.subtitle_dropdown = ttk.Combobox(self, state="readonly", width=40)
        self.canvas.create_window(310, y_pos, window=self.subtitle_dropdown, anchor="w")
        y_pos += 30

        bitrate_label = tk.Label(self, text="Bitrate (kbps):")
        self.canvas.create_window(300, y_pos, window=bitrate_label, anchor="e")
        self.bitrate_dropdown = ttk.Combobox(self, state="readonly")
        self.bitrate_dropdown['values'] = [str(b) for b in range(1000, 4500, 500)]
        self.bitrate_dropdown.set("2000")
        self.canvas.create_window(310, y_pos, window=self.bitrate_dropdown, anchor="w")
        y_pos += 40

        self.update_streams_btn = tk.Button(
            self, text="Update Streams", bg="#90ee90", command=self.update_streams
        )
        # Shift button slightly left for better spacing
        self.canvas.create_window(300, y_pos, window=self.update_streams_btn, anchor="n")
        self.update_streams_btn.config(state="disabled")
        y_pos += 40

        self.convert_video_btn = tk.Button(
            self, text="Convert to HEVC", bg="#add8e6", command=self.convert_to_hevc
        )
        # Align convert button with updated streams button
        self.canvas.create_window(300, y_pos, window=self.convert_video_btn, anchor="n")
        self.convert_video_btn.config(state="disabled")

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self, variable=self.progress_var, maximum=100, mode="determinate", length=300
        )
        y_pos += 50
        self.progress_bar_window = self.canvas.create_window(400, y_pos, window=self.progress_bar, anchor="n")
        self.canvas.itemconfigure(self.progress_bar_window, state="hidden")
        y_pos += 30

        self.status_label = tk.Label(self, text="", anchor="center")
        self.canvas.create_window(400, y_pos, window=self.status_label, anchor="n")

        # Exit button from original demo
        self.exit_btn = tk.Button(self, text="Exit", command=self.quit_app, width=6)
        self.exit_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        # track processed directories for cleanup after exiting
        self.processed_dirs = set()
        self.status_log = []
        self.convert_log = []
        self.streams_log = []

        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    def _load_last_folder(self):
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text())
                return data.get("last_folder")
            except Exception:
                return None
        return None

    def _save_last_folder(self, folder: str):
        SETTINGS_FILE.write_text(json.dumps({"last_folder": folder}))

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

    def write_convert_log(self):
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        with open(documents_dir / "convert.json", "w", encoding="utf-8") as f:
            json.dump(self.convert_log, f, indent=2)

    def write_streams_log(self):
        documents_dir = Path.home() / "Documents"
        documents_dir.mkdir(parents=True, exist_ok=True)
        with open(documents_dir / "streams.json", "w", encoding="utf-8") as f:
            json.dump(self.streams_log, f, indent=2)

    def ask_commit_updates(self):
        if not self.processed_dirs:
            return
        if messagebox.askyesno(
            "Processing Complete",
            "All work completed. Commit updates to original files?",
        ):
            self.commit_converted_files()
            messagebox.showinfo(
                "Commit Complete",
                "Converted files have been moved back.",
            )

    def quit_app(self):
        self.ask_commit_updates()
        self.write_convert_log()
        self.write_streams_log()
        self.destroy()

    def select_path(self):
        folder = filedialog.askdirectory(
            title="Select folder with video files",
            initialdir=self._load_last_folder() or str(DEFAULT_VIDEO_DIR),
        )
        if not folder:
            return

        self._save_last_folder(folder)
        self.selected_folder = folder
        self.select_file_btn.config(text=f"Select Folder\n{folder}")

        self.video_files = sorted(
            [str(f) for f in Path(folder).rglob("*.mkv")] + [str(f) for f in Path(folder).rglob("*.mp4")]
        )
        if not self.video_files:
            self.log_status("error", message="No MKV or MP4 files found in selected folder.")
            self.convert_video_btn.config(state="disabled")
            self.update_streams_btn.config(state="disabled")
            return

        self.current_index = 0
        self.selected_file = self.video_files[self.current_index]
        self.current_file = self.selected_file
        self.populate_stream_dropdowns(self.selected_file)
        self.convert_video_btn.config(state="normal")
        self.update_streams_btn.config(state="normal")

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
                creationflags=CREATE_NO_WINDOW,
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
                creationflags=CREATE_NO_WINDOW,
            )
            return result.stdout.strip().lower()
        except Exception:
            return None

    def get_duration(self, filepath):
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
                creationflags=CREATE_NO_WINDOW,
            )
            return float(result.stdout.strip())
        except Exception as e:
            print(f"ffprobe duration error for {filepath}:", e)
            return None

    def time_to_seconds(self, time_str):
        try:
            h, m, s = time_str.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            return None

    def populate_stream_dropdowns(self, filepath):
        audio_streams = self.run_ffprobe(filepath, "a")
        subtitle_streams = self.run_ffprobe(filepath, "s")

        audio_options = []
        subtitle_options = [""]
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

        self.audio_dropdown['values'] = audio_options
        if default_audio and default_audio in audio_options:
            self.audio_dropdown.set(default_audio)
        elif audio_options:
            self.audio_dropdown.set(audio_options[0])

        self.subtitle_dropdown['values'] = subtitle_options
        if default_subtitle and default_subtitle in subtitle_options:
            self.subtitle_dropdown.set(default_subtitle)
        elif len(subtitle_options) > 1:
            self.subtitle_dropdown.set(subtitle_options[1])
        elif subtitle_options:
            self.subtitle_dropdown.set(subtitle_options[0])

    def convert_to_hevc(self):
        if not getattr(self, "video_files", None):
            self.log_status("error", message="Please select a folder first.")
            messagebox.showwarning("No Folder Selected", "Please select a folder first.")
            return

        self.status_label.config(text="Converting... please wait")
        self.progress_bar['maximum'] = len(self.video_files) * 100
        self.progress_var.set(0)
        self.canvas.itemconfigure(self.progress_bar_window, state="normal")
        self.convert_video_btn.config(state="disabled")
        self.update_streams_btn.config(state="disabled")
        self.update()

        self.convert_log = []

        for idx, input_file in enumerate(self.video_files, start=1):
            self.current_file = input_file
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
                    creationflags=CREATE_NO_WINDOW,
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
                self.log_status("error", input_file=input_file, message=f"Codec check failed: {e}")
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
                self.bitrate_dropdown.get() + "k",
                output_path,
            ]

            try:
                process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                )
                for line in process.stderr:
                    fps, time_pos = self.parse_ffmpeg_progress(line)
                    if fps or time_pos:
                        self.status_label.config(
                            text=f"{os.path.basename(input_file)} - fps: {fps} time: {time_pos}"
                        )
                        if duration and time_pos:
                            secs = self.time_to_seconds(time_pos)
                            if secs is not None:
                                progress = min(secs / duration, 1.0)
                                self.progress_var.set(int((idx - 1 + progress) * 100))
                        self.update()
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
                self.log_status("error", input_file=input_file, message="FFmpeg failed during conversion")

            self.progress_var.set(idx * 100)
            self.update()

        self.ask_commit_updates()
        self.write_convert_log()
        self.status_label.config(text="Done")
        self.canvas.itemconfigure(self.progress_bar_window, state="hidden")
        self.convert_video_btn.config(state="normal")
        self.update_streams_btn.config(state="normal")

    def update_streams(self):
        if not getattr(self, "video_files", None):
            self.log_status("error", message="Please select a folder first.")
            messagebox.showwarning("No Folder Selected", "Please select a folder first.")
            return

        self.status_label.config(text="Updating streams... please wait")
        self.progress_bar['maximum'] = len(self.video_files) * 100
        self.progress_var.set(0)
        self.canvas.itemconfigure(self.progress_bar_window, state="normal")
        self.convert_video_btn.config(state="disabled")
        self.update_streams_btn.config(state="disabled")
        self.update()

        self.streams_log = []

        audio = self.audio_dropdown.get()
        subtitle = self.subtitle_dropdown.get()
        if not audio:
            self.log_status("error", message="Please select an audio stream.")
            return

        remove_subtitles = subtitle.strip() == ""
        if not remove_subtitles and not subtitle:
            self.log_status("error", message="Please select both audio and subtitle streams.")
            return

        if not remove_subtitles:
            subtitle_index = subtitle.split(" ")[1]
        audio_index = audio.split(" ")[1]

        for idx, input_file in enumerate(self.video_files, start=1):
            self.current_file = input_file
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
            ]

            if not remove_subtitles:
                cmd.extend([
                    "-map",
                    f"0:{subtitle_index}",
                    "-c:s",
                    "copy",
                ])
            else:
                cmd.append("-sn")

            cmd.extend([
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-map_chapters",
                "0",
            ])
            if not remove_subtitles:
                cmd.extend(["-disposition:s:0", "forced"])
            cmd.append(output_path)

            try:
                process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                )
                for line in process.stderr:
                    fps, time_pos = self.parse_ffmpeg_progress(line)
                    if fps or time_pos:
                        self.status_label.config(
                            text=f"{os.path.basename(input_file)} - fps: {fps} time: {time_pos}"
                        )
                        if duration and time_pos:
                            secs = self.time_to_seconds(time_pos)
                            if secs is not None:
                                progress = min(secs / duration, 1.0)
                                self.progress_var.set(int((idx - 1 + progress) * 100))
                        self.update()
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
                self.log_status("error", input_file=input_file, message="FFmpeg failed during stream update")

            self.progress_var.set(idx * 100)
            self.update()

        self.ask_commit_updates()
        self.write_streams_log()
        self.status_label.config(text="Done")
        self.canvas.itemconfigure(self.progress_bar_window, state="hidden")
        self.convert_video_btn.config(state="normal")
        self.update_streams_btn.config(state="normal")

if __name__ == "__main__":
    img_path = Path(__file__).parent / "images" / "movie_theatre.png"
    app = TheatreApp(img_path)
    app.mainloop()
