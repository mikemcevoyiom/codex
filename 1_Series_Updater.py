import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
)


class SeriesUpdater(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Renamer")
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.folder_label = QLabel("")
        layout.addWidget(self.folder_label)

        self.rename_button = QPushButton("Rename Videos")
        self.rename_button.setStyleSheet("background-color: #90ee90;")
        self.rename_button.clicked.connect(self.rename_videos)
        layout.addWidget(self.rename_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(QApplication.quit)
        layout.addWidget(quit_button)

    def rename_videos(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return
        self.folder_label.setText(f"Selected Folder: {folder}")
        self.rename_files_in_directory(folder)

    def rename_files_in_directory(self, folder_path):
        try:
            central_output_folder = r"D:\\convert\\anime"
            os.makedirs(central_output_folder, exist_ok=True)
            if os.access(central_output_folder, os.W_OK):
                cmd = [
                    "filebot",
                    "-script",
                    "fn:amc",
                    "--output",
                    central_output_folder,
                    "--action",
                    "move",
                    "-non-strict",
                    "--log-file",
                    "amc.log",
                    "--db",
                    "TheTVDB",
                    "--def",
                    "movieFormat={ny}/{ny}",
                    "--def",
                    "seriesFormat={ny}/Season {s}/{ny} - {s00e00} - {t}",
                    "--def",
                    "animeFormat={ny}/Season {s}/{ny} - {s00e00} - {t}",
                    "--def",
                    "skipExtract=y",
                    "--def",
                    "minLengthMS=60000",
                    "--def",
                    "clean=y",
                    "--def",
                    "deleteAfterExtract=y",
                    "--def",
                    "unsorted=y",
                    folder_path,
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    self.result_label.setText("Renaming complete.")
                else:
                    self.result_label.setText(f"Error: {result.stderr}")
            else:
                self.result_label.setText(
                    "Error: Central output folder is not writable."
                )
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeriesUpdater()
    window.show()
    sys.exit(app.exec_())
