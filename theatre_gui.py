import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

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
        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.exit_btn = tk.Button(self, text="Exit", command=self.destroy, width=6)
        # place button bottom right with a little padding
        self.exit_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

if __name__ == "__main__":
    img_path = Path(__file__).parent / "images" / "movie_theatre.png"
    app = TheatreApp(img_path)
    app.mainloop()
