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
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)
        self.select_file_btn = tk.Button(self.frame, text="Select Folder", command=self.select_path)
        self.select_file_btn.grid(row=0, column=0, columnspan=2, pady=5)
        self.audio_label = tk.Label(self.frame, text="Select Audio Stream:")
        self.audio_label.grid(row=1, column=0, sticky="e")
        self.audio_var = tk.StringVar()
        self.audio_dropdown = tk.OptionMenu(self.frame, self.audio_var, "")
        self.audio_dropdown.grid(row=1, column=1, sticky="w")
        self.subtitle_label = tk.Label(self.frame, text="Select Subtitle Stream:")
        self.subtitle_label.grid(row=2, column=0, sticky="e")
        self.subtitle_var = tk.StringVar()
        self.subtitle_dropdown = tk.OptionMenu(self.frame, self.subtitle_var, "")
        self.subtitle_dropdown.grid(row=2, column=1, sticky="w")
        
        self.bitrate_label = tk.Label(self.frame, text="Bitrate (kbps):")
        self.bitrate_label.grid(row=3, column=0, sticky="w", pady=5)
        self.bitrate_var = tk.StringVar()
        self.bitrate_var.set("2000")
        self.bitrate_dropdown = tk.OptionMenu(self.frame, self.bitrate_var, *[str(b) for b in range(1000, 4500, 500)])
        self.bitrate_dropdown.config(width=10)
        self.bitrate_dropdown.grid(row=3, column=1, sticky="w", pady=5)
        self.verify_var = tk.BooleanVar(value=True)
        self.verify_check = tk.Checkbutton(self.frame, text="Verify stream order after conversion", variable=self.verify_var)
        self.verify_check.grid(row=6, column=0, columnspan=2, sticky="w")
        self.convert_btn = tk.Button(self.frame, text="Convert Selected", command=self.convert_selected)
    
        self.convert_btn.grid(row=4, column=0, pady=10)
        self.exit_btn = tk.Button(self.frame, text="Exit", command=self.root.quit)
        self.exit_btn.grid(row=4, column=1, pady=10)
    def select_path(self):
        from pathlib import Path
        from pathlib import Path
        
        folder = filedialog.askdirectory(title="Select folder with video files")
        if not folder:
            return
        
        self.video_files = sorted(
            [str(f) for f in Path(folder).rglob("*.mkv")] +
            [str(f) for f in Path(folder).rglob("*.mp4")]
        )
        if not self.video_files:
            messagebox.showerror("No Files", "No MKV or MP4 files found in selected folder.")
            return
        self.selected_file = self.video_files[0]
        self.populate_stream_dropdowns(self.selected_file)
    
        if not self.video_files:
            return
            messagebox.showerror("No Files", "No MKV or MP4 files found in selected folder.")
            return
        self.selected_file = self.video_files[0]
        
    
        
                        
            
    def run_ffprobe(self, filepath, stream_type):
        try:
            result = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", stream_type,
                "-show_entries", "stream=index,codec_type:stream_tags=language,title",
                "-of", "json", filepath
            ], capture_output=True, text=True, check=True)
            return json.loads(result.stdout).get("streams", [])
        except subprocess.CalledProcessError as e:
            print(f"ffprobe failed for stream type '{stream_type}':", e)
            return []
    def populate_stream_dropdowns(self, filepath):
        audio_streams = self.run_ffprobe(filepath, "a")
        subtitle_streams = self.run_ffprobe(filepath, "s")
        audio_options = []
        subtitle_options = []
        for stream in audio_streams:
            index = stream.get("index")
            lang = stream.get("tags", {}).get("language", "und")
            title = stream.get("tags", {}).get("title", "")
            label = f"Stream {index} - {lang}"
            if 'forced' in title.lower():
                label += ' [FORCED]'
            if title:
                label += f' ({title})'
                label += f' ({title})'
                label += f" ({title})"
            audio_options.append(label)
        for stream in subtitle_streams:
            index = stream.get("index")
            lang = stream.get("tags", {}).get("language", "und")
            title = stream.get("tags", {}).get("title", "")
            label = f"Stream {index} - {lang}"
            if 'forced' in title.lower():
                label += ' [FORCED]'
            if title:
                label += f' ({title})'
                label += f" ({title})"
            subtitle_options.append(label)
        self.audio_var.set(audio_options[0] if audio_options else "")
        menu = self.audio_dropdown["menu"]
        menu.delete(0, "end")
        for opt in audio_options:
            menu.add_command(label=opt, command=lambda value=opt: self.audio_var.set(value))
        self.subtitle_var.set(subtitle_options[0] if subtitle_options else "")
        menu = self.subtitle_dropdown["menu"]
        menu.delete(0, "end")
        for opt in subtitle_options:
            menu.add_command(label=opt, command=lambda value=opt: self.subtitle_var.set(value))
    def convert_selected(self):
        first_converted_file = None
        if not hasattr(self, 'selected_file'):
            messagebox.showwarning("No File", "Please select a video file first.")
            return
        audio = self.audio_var.get()
        subtitle = self.subtitle_var.get()

        if not audio or not subtitle:
            messagebox.showwarning("Selection Missing", "Please select both audio and subtitle streams.")
            return

        subtitle_index = subtitle.split(" ")[1]
        # Extract stream indices
        audio_index = audio.split(" ")[1]
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=codec_name",
                    "-of", "default=noprint_wrappers=1:nokey=1", self.selected_file
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            codec = result.stdout.strip().lower()
            if codec in ("hevc", "av1"):
                messagebox.showinfo("Skipped", f"Skipping {self.selected_file} (already {codec.upper()})")
                return
        except Exception as e:
            messagebox.showwarning("Error", f"Codec check failed: {e}")
            return
        self.converted_dir = os.path.join(os.path.dirname(self.selected_file), "converted")
        os.makedirs(self.converted_dir, exist_ok=True)
        output_path = os.path.join(self.converted_dir, os.path.basename(self.selected_file))
        if first_converted_file is None:
            first_converted_file = output_path
        cmd = [
            "ffmpeg", "-y", "-i", self.selected_file,
            "-map", f"0:{audio_index}", "-map", f"0:{subtitle_index}", "-map", "0:v:0",
            "-c:v", "hevc_amf", "-c:a", "copy", "-c:s", "copy", "-map_chapters", "0", "-usage", "transcoding", "-b:v", self.bitrate_var.get() + "k",
            "-disposition:s:0", "forced",
            output_path
        ]
        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Success", "Conversion complete:\n" + first_converted_file)
        except subprocess.CalledProcessError as e:
            print("FFmpeg error:", e)
            messagebox.showerror("Error", "FFmpeg failed during conversion.")
    def verify_stream_order(self, first_converted_file):
        import subprocess, json
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_streams", "-select_streams", "v:a:s",
                "-of", "json", first_converted_file
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            expected_order = ["video", "audio", "subtitle"]
            actual_order = {s["index"]: s["codec_type"] for s in data.get("streams", [])}
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

    # Overwrite originals with converted files and delete converted folder if empty
    import os, shutil
    if hasattr(app, "converted_dir") and app.converted_dir and os.path.isdir(app.converted_dir):
        for file in os.listdir(app.converted_dir):
            src_path = os.path.join(app.converted_dir, file)
            dst_path = os.path.join(os.path.dirname(app.converted_dir), file)
            shutil.move(src_path, dst_path)
        try:
            os.rmdir(app.converted_dir)
        except OSError:
            print(f"Could not remove {app.converted_dir} — it may not be empty.")
