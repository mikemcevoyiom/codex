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
    QComboBox,
)


class SeriesUpdater(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Renamer")
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.folder_label = QLabel("")
        layout.addWidget(self.folder_label)

        self.series_button = QPushButton("Find Series")
        self.series_button.setStyleSheet("background-color: #add8e6;")
        self.series_button.clicked.connect(self.find_options)
        layout.addWidget(self.series_button)

        self.choice_dropdown = QComboBox()
        self.choice_dropdown.hide()
        layout.addWidget(self.choice_dropdown)

        self.rename_button = QPushButton("Rename Using Selection")
        self.rename_button.setStyleSheet("background-color: #90ee90;")
        self.rename_button.clicked.connect(self.rename_with_selection)
        self.rename_button.setEnabled(False)
        layout.addWidget(self.rename_button)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(QApplication.quit)
        layout.addWidget(quit_button)

    def find_options(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return

        self.selected_folder = folder
        self.folder_label.setText(f"Selected Folder: {folder}")

        search_term = os.path.basename(folder)
        # Use TheMovieDB for both series and movies to avoid TheTVDB failures
        db = "TheMovieDB"

        try:
            cmd = ["filebot", "-list", "--q", search_term, "--db", db]
            result = subprocess.run(cmd, capture_output=True, text=True)
            options = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if options:
                self.choice_dropdown.clear()
                self.choice_dropdown.addItems(options)
                self.choice_dropdown.show()
                self.rename_button.setEnabled(True)
                self.result_label.setText("")
            else:
                self.result_label.setText("No matches found")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")

    def rename_with_selection(self):
        if not getattr(self, "selected_folder", None):
            return
        selection = self.choice_dropdown.currentText()
        # Always use TheMovieDB when renaming to ensure consistent results
        db = "TheMovieDB"
        self.rename_files_in_directory(self.selected_folder, selection, db)
        self.choice_dropdown.hide()
        self.choice_dropdown.clear()
        self.rename_button.setEnabled(False)

    def rename_files_in_directory(self, folder_path, search_name=None, db="TheMovieDB"):
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
                    db,
                    "--q",
                    search_name if search_name else os.path.basename(folder_path),
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
