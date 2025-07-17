import tkinter as tk
from tkinter import filedialog
import os
import subprocess
import shutil
from openpyxl import Workbook

# Create the main application window
root = tk.Tk()
root.title("Video Renamer")

# Store the selected folder path
selected_folder_path = None

# Function to open a folder dialog and start the video file renaming process
def rename_videos():
    global selected_folder_path
    folder_path = filedialog.askdirectory()
    selected_folder_path = folder_path
    folder_label.config(text="Selected Folder: " + folder_path)
    rename_files_in_directory(folder_path)

# Function to rename video files in a folder and its subfolders using FileBot
def rename_files_in_directory(folder_path):
    try:
        # Set the central location for temporary output
        central_output_folder = r'D:\convert\anime'

        # Ensure that the central output folder exists and is writable
        if not os.path.exists(central_output_folder):
            os.makedirs(central_output_folder)

        if os.access(central_output_folder, os.W_OK):
            # Construct the FileBot command to rename video files in the chosen directory and its subdirectories
            cmd = f'filebot -script fn:amc --output "{central_output_folder}" --action move -non-strict --log-file amc.log --db TheTVDB --def movieFormat="{{ny}}/{{ny}}" --def seriesFormat="{{ny}}/Season {{s}}/{{ny}} - {{s00e00}} - {{t}}" --def animeFormat="{{ny}}/Season {{s}}/{{ny}} - {{s00e00}} - {{t}}" --def skipExtract=y --def minLengthMS=60000 --def clean=y --def deleteAfterExtract=y --def unsorted=y "{folder_path}"'

            os.system(cmd)

            result_label.config(text="Renaming complete.")
        else:
            result_label.config(text=f"Error: Central output folder is not writable.")
    except Exception as e:
        result_label.config(text=f"Error: {str(e)}")

# Function to quit the application
def quit_application():
    root.quit()

# Create a label to display the selected folder's path
folder_label = tk.Label(root, text="", wraplength=400)
folder_label.pack(pady=10)

# Create a button to start the video file renaming process
rename_button = tk.Button(root, text="Rename Videos", command=rename_videos)
rename_button.pack(pady=10)

# Create a label to display the result
result_label = tk.Label(root, text="")
result_label.pack(pady=10)

# Create a button to quit the application
quit_button = tk.Button(root, text="Quit", command=quit_application)
quit_button.pack(pady=10)

# Start the main event loop
root.mainloop()
