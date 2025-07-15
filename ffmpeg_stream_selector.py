from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import json


class StreamSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FFmpeg Stream Selector")
        # Increase default window size for better spacing
        self.root.geometry("450x300")
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10, fill="both", expand=True)
        # Allow grid columns to expand proportionally
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.select_file_btn = tk.Button(
            self.frame, text="Select Folder", command=self.select_path
        )
        self.select_file_btn.grid(row=0, column=0, columnspan=2, pady=5)
        self.audio_label = tk.Label(self.frame, text="Select Audio Stream:")
        self.audio_label.grid(row=1, column=0, sticky="e")
        self.audio_var = tk.StringVar()
        self.audio_dropdown = tk.OptionMenu(self.frame, self.audio_var, "")
        self.audio_dropdown.grid(row=1, column=1, sticky="ew")
        self.subtitle_label = tk.Label(self.frame, text="Select Subtitle Stream:")
        self.subtitle_label.grid(row=2, column=0, sticky="e")
        self.subtitle_var = tk.StringVar()
        self.subtitle_dropdown = tk.OptionMenu(self.frame, self.subtitle_var, "")
        self.subtitle_dropdown.grid(row=2, column=1, sticky="ew")

        self.bitrate_label = tk.Label(self.frame, text="Bitrate (kbps):")
        self.bitrate_label.grid(row=3, column=0, sticky="w", pady=5)
        self.bitrate_var = tk.StringVar()
        self.bitrate_var.set("2000")
        self.bitrate_dropdown = tk.OptionMenu(
            self.frame, self.bitrate_var, *[str(b) for b in range(1000, 4500, 500)]
        )
        self.bitrate_dropdown.config(width=10)
        self.bitrate_dropdown.grid(row=3, column=1, sticky="ew", pady=5)
        self.verify_var = tk.BooleanVar(value=True)
        self.verify_check = tk.Checkbutton(
            self.frame,
            text="Verify stream order after conversion",
            variable=self.verify_var,
        )
        self.verify_check.grid(row=5, column=0, columnspan=2, sticky="w")
        self.convert_video_btn = tk.Button(
            self.frame,
            text="Convert to HEVC",
            command=self.convert_to_hevc,
            bg="#add8e6",
        )
        self.update_streams_btn = tk.Button(
            self.frame,
            text="Update Streams",
            command=self.update_streams,
            bg="#90ee90",
        )

        # Track processed directories for cleanup after exiting
        self.processed_dirs = set()

        # Collect status information for JSON output
        self.status_log = []

        self.convert_video_btn.grid(row=4, column=0, pady=10, sticky="ew")
        self.update_streams_btn.grid(row=4, column=1, pady=10, sticky="ew")
        self.exit_btn = tk.Button(self.frame, text="Exit", command=self.quit_app)
        self.exit_btn.grid(row=6, column=0, columnspan=2, pady=10)

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
        if messagebox.askyesno(
            "Processing Complete",
            "All work completed. Commit updates to original files?",
        ):
            self.commit_converted_files()
            self.write_status_log()
            messagebox.showinfo(
                "Commit Complete", "Converted files have been moved back."
            )

    def quit_app(self):
        """Handle exit button click."""
        self.ask_commit_updates()
        self.root.quit()

    def select_path(self):
        from pathlib import Path

        folder = filedialog.askdirectory(title="Select folder with video files")
        if not folder:
            return

        self.video_files = sorted(
            [str(f) for f in Path(folder).rglob("*.mkv")]
            + [str(f) for f in Path(folder).rglob("*.mp4")]
        )
        if not self.video_files:
            self.log_status(
                "error",
                message="No MKV or MP4 files found in selected folder."
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

        self.audio_var.set(
            default_audio if default_audio else (audio_options[0] if audio_options else "")
        )
        menu = self.audio_dropdown["menu"]
        menu.delete(0, "end")
        for opt in audio_options:
            menu.add_command(
                label=opt, command=lambda value=opt: self.audio_var.set(value)
            )
        self.subtitle_var.set(
            default_subtitle
            if default_subtitle
            else (subtitle_options[0] if subtitle_options else "")
        )
        menu = self.subtitle_dropdown["menu"]
        menu.delete(0, "end")
        for opt in subtitle_options:
            menu.add_command(
                label=opt, command=lambda value=opt: self.subtitle_var.set(value)
            )

    def convert_to_hevc(self):
        if not getattr(self, "video_files", None):
            self.log_status(
                "error",
                message="Please select a folder first."
            )
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
                        message=f"Already {codec.upper()}"
                    )
                    continue
            except Exception as e:
                self.log_status(
                    "error",
                    input_file=input_file,
                    message=f"Codec check failed: {e}"
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
                self.bitrate_var.get() + "k",
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
            self.log_status(
                "error",
                message="Please select a folder first."
            )
            return

        audio = self.audio_var.get()
        subtitle = self.subtitle_var.get()
        if not audio or not subtitle:
            self.log_status(
                "error",
                message="Please select both audio and subtitle streams."
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
    root = tk.Tk()
    app = StreamSelectorApp(root)
    root.mainloop()

    # Handle any remaining processed files when the window is closed directly
    if getattr(app, "processed_dirs", None):
        app.commit_converted_files()
        app.write_status_log()
