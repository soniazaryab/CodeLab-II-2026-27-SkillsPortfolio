"""
Exercise 2 - Alexa, tell me a joke

Click the title to start. The jokes screen shows the start of a random joke.
"Show Punchline" reveals the end, and "Next Joke" tells a new one.
"Quit" goes to the end screen, and "Exit" closes the program.

The jokes come from randomJokes.txt (one joke per line, setup and punchline
split by a question mark).
"""

import os
import random
import tkinter as tk
from tkinter import messagebox

import pygame                        # plays the sounds and music
from PIL import Image, ImageTk       # loads and resizes the background pictures

# ----- files and folders -----
FOLDER = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(FOLDER, "assets")
AUDIO_FOLDER = os.path.join(ASSETS, "audio")
JOKES_FILE = "randomJokes.txt"

# ----- settings -----
TEXT_COLOUR = "#2b1b5a"      # dark purple
FONT = "Helvetica"
MUSIC_VOLUME = 0.25          # 0 is silent, 1 is full volume
LAUGH_EARLY_MS = 600         # the laugh starts this many milliseconds before the voice ends

# My pictures are 1920 x 1080, so all positions below are for that size.
# Each button is (centre x, centre y, width, height).
TITLE_BUTTON = (1088, 440, 900, 330)
SHOW_PUNCHLINE_BUTTON = (695, 553, 494, 129)
NEXT_JOKE_BUTTON = (1242, 553, 503, 129)
QUIT_BUTTON = (1730, 244, 290, 132)
EXIT_BUTTON = (1526, 660, 680, 195)


def stop_windows_blurring():
    """On Windows, stop display scaling from making the window look blurry."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass     # not Windows, so there is nothing to do


def find_jokes_file():
    """Look for randomJokes.txt in a few folders and return its path."""
    folders = [FOLDER,
               os.path.join(FOLDER, "resources"),
               os.path.join(os.path.dirname(FOLDER), "resources"),
               os.path.dirname(FOLDER)]
    for folder in folders:
        path = os.path.join(folder, JOKES_FILE)
        if os.path.exists(path):
            return path
    return None


def load_jokes(path):
    """Read the file and return a list of (setup, punchline) pairs."""
    jokes = []
    with open(path, encoding="utf-8-sig", errors="replace") as file:
        for line in file:
            if "?" in line:
                # split at the first question mark only
                setup, punchline = line.split("?", 1)
                if punchline.strip() != "":
                    jokes.append((setup.strip() + "?", punchline.strip()))
    return jokes


class JokeApp:
    def __init__(self, root, jokes):
        self.root = root
        self.jokes = jokes
        self.buttons = []            # the clickable areas on the current screen
        self.joke_number = 1         # which joke is on screen (counting from 1)
        self.unused_jokes = []       # joke numbers not told yet in this round
        self.laugh_timer = None      # remembers the waiting laugh so we can cancel it
        self.resize_timer = None     # remembers the waiting resize (see on_resize)
        self.fullscreen = False      # True while the window is in full screen
        self.screen = "title"        # which screen is showing: title, jokes or end
        self.setup_line = ""         # the joke text on screen, kept so we can redraw it
        self.punchline_line = ""

        # Start with the largest picture that fits the screen (but never bigger than 1920 x 1080)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        scale = min(1, screen_width / 1920, (screen_height - 100) / 1080)

        root.title("Alexa, tell me a joke")
        root.configure(bg="black")
        root.geometry(f"{int(1920 * scale)}x{int(1080 * scale)}")
        root.minsize(640, 360)
        root.bind("<F11>", self.toggle_fullscreen)       # F11 switches full screen on or off
        root.bind("<Escape>", self.leave_fullscreen)     # Escape leaves full screen

        # The canvas holds the picture. place() keeps it in the middle, so if the
        # window is not the same shape as the picture the extra space shows as black borders.
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.set_size(scale)
        self.start_music()
        self.show_title()

        # From now on, whenever the window changes size (maximise, restore or dragging
        # the edge) on_resize runs. This is bound last so it doesn't run during setup.
        root.bind("<Configure>", self.on_resize)

    # ----- window size -----
    def set_size(self, scale):
        """Use this scale for everything: the canvas, the three pictures and the text."""
        self.scale = scale
        self.width = int(1920 * scale)
        self.height = int(1080 * scale)
        self.canvas.config(width=self.width, height=self.height)
        # The pictures are saved on self so Python doesn't delete them.
        self.title_picture = self.load_picture("bg_title.png")
        self.jokes_picture = self.load_picture("bg_jokes.png")
        self.end_picture = self.load_picture("bg_end.png")

    def toggle_fullscreen(self, event=None):
        """Switch between full screen and the normal window."""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def leave_fullscreen(self, event=None):
        """Go back to the normal window (does nothing if we are already in it)."""
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def on_resize(self, event):
        """The window changed size. Wait until the changing stops, then fit the picture."""
        if event.widget is not self.root:       # ignore events from things inside the window
            return
        if self.resize_timer is not None:
            self.root.after_cancel(self.resize_timer)
        # Dragging an edge fires this many times a second, so we wait 200 ms of calm
        self.resize_timer = self.root.after(200, self.fit_to_window)

    def fit_to_window(self):
        """Make the picture as big as the window allows, then draw the screen again."""
        self.resize_timer = None
        scale = min(self.root.winfo_width() / 1920, self.root.winfo_height() / 1080, 2)
        if abs(scale - self.scale) < 0.01:      # the picture already fits
            return
        self.set_size(scale)
        if self.screen == "title":
            self.show_title()
        elif self.screen == "jokes":
            self.show_jokes()
        else:
            self.show_end()

    # ----- helpers -----
    def load_picture(self, filename):
        """Open a picture and resize it to fit the window."""
        image = Image.open(os.path.join(ASSETS, filename))
        image = image.resize((self.width, self.height), Image.LANCZOS)   # LANCZOS keeps it sharp
        return ImageTk.PhotoImage(image)

    def write(self, x, y, text, size, wrap=0):
        """Write text on the canvas. x, y and size are for the 1920 x 1080 design."""
        return self.canvas.create_text(
            x * self.scale, y * self.scale, text=text, fill=TEXT_COLOUR,
            font=(FONT, -int(size * self.scale), "bold"),   # minus = size in pixels
            width=wrap * self.scale, justify="center")

    def add_button(self, box, command, text="", size=38):
        """Make an invisible clickable area (the real button is part of the picture)."""
        x, y, width, height = box
        if text != "":
            self.write(x, y, text, size)
        # save the corners of the area, so on_click can check if a click landed inside
        left = (x - width / 2) * self.scale
        top = (y - height / 2) * self.scale
        right = (x + width / 2) * self.scale
        bottom = (y + height / 2) * self.scale
        self.buttons.append((left, top, right, bottom, command))

    def on_click(self, event):
        """Runs on every click. Finds the button that was clicked and runs its command."""
        for left, top, right, bottom, command in self.buttons:
            if left <= event.x <= right and top <= event.y <= bottom:
                command()
                break

    def on_mouse_move(self, event):
        """Show a hand cursor when the mouse is over a button, otherwise the normal arrow."""
        cursor = ""
        for left, top, right, bottom, command in self.buttons:
            if left <= event.x <= right and top <= event.y <= bottom:
                cursor = "hand2"
        self.canvas.config(cursor=cursor)

    def new_screen(self, name, picture):
        """Clear the canvas and draw a new background picture."""
        self.screen = name
        self.canvas.delete("all")
        self.buttons = []
        self.canvas.create_image(0, 0, image=picture, anchor="nw")

    # ----- sound -----
    def start_music(self):
        """Play the background music over and over."""
        pygame.mixer.init()
        path = os.path.join(AUDIO_FOLDER, "bg_music.mp3")
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)      # -1 means repeat forever
   # AI-assisted (Claude): uses the pygame mixer to play the background music in a loop.

    def play_sound(self, name):
        """Play a sound from the audio folder. Returns the sound (or None if not found)."""
        path = os.path.join(AUDIO_FOLDER, name + ".mp3")
        if not os.path.exists(path):
            return None
        sound = pygame.mixer.Sound(path)
        sound.play()
        return sound

    def stop_sounds(self):
        """Stop the voice and cancel a laugh that is still waiting to play."""
        if self.laugh_timer is not None:
            self.root.after_cancel(self.laugh_timer)
            self.laugh_timer = None
        pygame.mixer.stop()          # stops the voice and laugh, not the music

    # ----- screens -----
    def show_title(self):
        self.new_screen("title", self.title_picture)
        self.add_button(TITLE_BUTTON, self.start_jokes)

    def start_jokes(self):
        """Go to the jokes screen and tell the first joke."""
        self.show_jokes()
        self.next_joke()

    def show_jokes(self):
        """Draw the jokes screen with whatever joke text is stored."""
        self.new_screen("jokes", self.jokes_picture)
        self.setup_text = self.write(948, 313, self.setup_line, 56, wrap=1000)
        self.punchline_text = self.write(965, 765, self.punchline_line, 56, wrap=1000)
        self.add_button(SHOW_PUNCHLINE_BUTTON, self.show_punchline, "Show Punchline")
        self.add_button(NEXT_JOKE_BUTTON, self.next_joke, "Next Joke")
        self.add_button(QUIT_BUTTON, self.show_end, "Quit", 46)

    def show_end(self):
        self.stop_sounds()
        self.new_screen("end", self.end_picture)
        self.add_button(EXIT_BUTTON, self.exit_program, "Exit", 64)

    # ----- the jokes -----
    def next_joke(self):
        """Pick a random joke and show only the setup."""
        self.stop_sounds()
        # When every joke has been told, shuffle all the numbers again for a new round.
        # pop() takes one number out of the list, so a joke can't repeat until the next round.
        if len(self.unused_jokes) == 0:
            self.unused_jokes = list(range(1, len(self.jokes) + 1))
            random.shuffle(self.unused_jokes)
        self.joke_number = self.unused_jokes.pop()
        self.setup_line, punchline = self.jokes[self.joke_number - 1]
        self.punchline_line = ""
        self.canvas.itemconfig(self.setup_text, text=self.setup_line)
        self.canvas.itemconfig(self.punchline_text, text="")
        self.play_sound(f"joke_{self.joke_number:02d}_setup")
        
    def show_punchline(self):
        """Show the punchline, read it out, then play the laugh when it has finished."""
        self.stop_sounds()
        setup, self.punchline_line = self.jokes[self.joke_number - 1]
        self.canvas.itemconfig(self.punchline_text, text=self.punchline_line)
        voice = self.play_sound(f"joke_{self.joke_number:02d}_punchline")
        wait = 0
        if voice is not None:
            length = int(voice.get_length() * 1000)   # length in milliseconds
            wait = max(0, length - LAUGH_EARLY_MS)    # start the laugh a bit early
        # after() runs the laugh once the wait time is over
        self.laugh_timer = self.root.after(wait, self.laugh)
   # AI-assisted (Claude): works out when the voice ends so the laugh can start a little early

    def laugh(self):
        self.laugh_timer = None
        self.play_sound("laugh")

    def exit_program(self):
        # Close a moment later, so the click finishes first (closing straight
        # away made the program crash when I tested it)
        self.root.after(10, self.root.destroy)


def main():
    stop_windows_blurring()      # must be done before the window is created
    root = tk.Tk()
    path = find_jokes_file()
    if path is None:
        messagebox.showerror("Error", "Could not find " + JOKES_FILE)
        return
    jokes = load_jokes(path)
    if len(jokes) == 0:
        messagebox.showerror("Error", "No jokes found in " + JOKES_FILE)
        return
    JokeApp(root, jokes)
    root.mainloop()


if __name__ == "__main__":
    main()