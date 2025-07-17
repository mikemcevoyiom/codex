import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
import subprocess
from openpyxl import Workbook


def run_code1():
    """Launch a video renamer window."""

    window = tk.Toplevel()
    window.title("Video Renamer")

    selected_folder_path = None

    def rename_videos():
        nonlocal selected_folder_path
        folder_path = filedialog.askdirectory(parent=window)
        selected_folder_path = folder_path
        folder_label.config(text="Selected Folder: " + folder_path)
        if folder_path:
            rename_files_in_directory(folder_path)

    def rename_files_in_directory(folder_path):
        try:
            central_output_folder = r'D:\Video\processed'

            if not os.path.exists(central_output_folder):
                os.makedirs(central_output_folder)

            if os.access(central_output_folder, os.W_OK):
                cmd = (
                    f'filebot -script fn:amc --output "{central_output_folder}" '
                    '--action move -non-strict --log-file amc.log --db TheTVDB '
                    '--def movieFormat="{{ny}}/{{ny}}" '
                    '--def seriesFormat="{{ny}}/Season {{s}}/{{ny}} - {{s00e00}} - {{t}}" '
                    '--def animeFormat="{{ny}}/Season {{s}}/{{ny}} - {{s00e00}} - {{t}}" '
                    '--def skipExtract=y --def minLengthMS=60000 --def clean=y '
                    '--def deleteAfterExtract=y --def unsorted=y '
                    f'"{folder_path}"'
                )
                os.system(cmd)
                result_label.config(text="Renaming complete.")
            else:
                result_label.config(
                    text="Error: Central output folder is not writable.")
        except Exception as e:
            result_label.config(text=f"Error: {str(e)}")

    folder_label = tk.Label(window, text="", wraplength=400)
    folder_label.pack(pady=10)

    rename_button = tk.Button(window, text="Rename Videos", command=rename_videos)
    rename_button.pack(pady=10)

    result_label = tk.Label(window, text="")
    result_label.pack(pady=10)

    quit_button = tk.Button(window, text="Quit", command=window.destroy)
    quit_button.pack(pady=10)


def run_code2():
    # TODO: replace with actual code
    messagebox.showinfo("Code 2", "Code 2 executed")


def run_code3():
    # TODO: replace with actual code
    messagebox.showinfo("Code 3", "Code 3 executed")


def create_gui():
    root = tk.Tk()
    root.title("Code Launcher")

    # Make the window bigger than the default size
    root.geometry("600x300")

    # Frame to hold the code buttons together
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)

    btn1 = tk.Button(button_frame, text="Code 1", width=20, command=run_code1)
    btn1.pack(pady=5)

    btn2 = tk.Button(button_frame, text="Code 2", width=20, command=run_code2)
    btn2.pack(pady=5)

    btn3 = tk.Button(button_frame, text="Code 3", width=20, command=run_code3)
    btn3.pack(pady=5)

    # Exit button placed at the bottom-right corner
    exit_btn = tk.Button(root, text="Exit", width=10, command=root.quit)
    exit_btn.pack(side="bottom", anchor="e", padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()