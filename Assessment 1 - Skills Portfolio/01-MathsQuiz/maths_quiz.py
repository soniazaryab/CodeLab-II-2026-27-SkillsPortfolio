"""
Exercise 1 - Maths Quiz (themed, animated GUI version)

A Tkinter quiz of 10 addition/subtraction questions with three difficulty levels.
Screens: title -> instructions -> difficulty menu -> quiz -> results.

Scoring:  10 points for a correct answer on the first attempt,
           5 points for a correct answer on the second attempt,
           0 points if both attempts are wrong.
"""

import math
import random
import sys
import time
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Game settings 
QUESTIONS_PER_QUIZ = 10
POINTS_FIRST_ATTEMPT = 10
POINTS_SECOND_ATTEMPT = 5
MAX_SCORE = QUESTIONS_PER_QUIZ * POINTS_FIRST_ATTEMPT  # 100
FEEDBACK_DELAY_MS = 1200  # pause so the player can read the feedback

# Difficulty level -> (name, smallest number, largest number)
LEVELS = {
    1: ("Easy", 1, 9),            # single digit
    2: ("Moderate", 10, 99),      # double digit
    3: ("Advanced", 1000, 9999),  # four digit
}

# Look and feel
ASSETS = Path(__file__).parent / "assets"

# Which image each screen uses. Screens can share a file
BACKGROUND_FILES = {
    "title": "bg_title.gif",
    "instructions": "bg_main.gif",
    "menu": "bg_main.gif",
    "results": "bg_main.gif",
    "quiz": "bg_quiz.png",
}

DESIGN_W, DESIGN_H = 1920, 1080   # all coordinates below are for this size
TASKBAR_ALLOWANCE = 100           # screen height kept free for title bar + taskbar

FONT_FILE = None                  # e.g. "my_font.ttf" (Windows only, from assets/)
FONT_NAME = "Helvetica"           # the font's family name once installed/loaded
FONT_STYLE = "bold"

FALLBACK_BG = "#0f0a2a"           # used when an image is missing
TEXT_COLOUR = "#ffffff"
QUIZ_TEXT_COLOUR = "#0f1b44"      # dark navy: readable on the light-blue screen
GOOD_COLOUR = "#15803d"           # dark green
WARN_COLOUR = "#b45309"           # dark amber
BAD_COLOUR = "#b91c1c"            # dark red
BUTTON_BG = "#5b21d9"
BUTTON_HOVER = "#7c3aed"
BUTTON_FG = "#ffffff"

# Animation settings
MAX_GIF_FRAMES = 30     # longer gifs are thinned out (every frame costs memory)
MIN_FRAME_DELAY_MS = 20
MIN_LOADING_SECONDS = 1.5   # keep the loading screen up at least this long (0 = off)
TITLE_BOB_PIXELS = 14    # how far the title text floats up and down

# Where things go, in 1920 x 1080 design coordinates (x, y).
# Adjust these to line up with your own artwork.
LAYOUT = {
    "title": (960, 300),
    "startButton": (960, 640),
    "instructionsText": (480, 190),        # top-left corner of the text block
    "continueButton": (960, 960),
    "menuHeading": (960, 250),
    "menuButtons": [(960, 450), (960, 600), (960, 750)],
    "questionCounter": (960, 250),
    "score": (540, 250),
    "problem": (960, 400),
    "answerBox": (960, 530),
    "submitButton": (960, 640),
    "feedback": (960, 730),
    "resultsScore": (960, 400),
    "resultsRank": (960, 540),
    "playAgainButton": (700, 760),
    "exitButton": (1220, 760),
}


# Pure helper functions (no GUI code, so they are easy to test with print())
def randomInt(level):
    """Return a random integer whose size depends on the difficulty level.

    Easy -> 1 digit, Moderate -> 2 digits, Advanced -> 4 digits.
    """
    _, minimum, maximum = LEVELS[level]
    return random.randint(minimum, maximum)


def decideOperation():
    """Randomly choose between addition and subtraction; returns '+' or '-'."""
    return random.choice(["+", "-"])


def getRank(score):
    """Turn a score out of 100 into a letter grade."""
    if score > 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def buildInstructions():
    """Build the instructions text from the settings so it never goes out of date."""
    lines = ["Instructions:", "1. Choose a difficulty level:"]
    for name, low, high in LEVELS.values():
        lines.append(f"      - {name}: numbers from {low} to {high}")
    lines += [
        "2. Answer the questions:",
        f"      - You get {QUESTIONS_PER_QUIZ} problems.",
        "      - Type your answer and press Submit (or Enter).",
        "3. Scoring:",
        f"      - Correct on the first try = {POINTS_FIRST_ATTEMPT} points",
        f"      - Correct on the second try = {POINTS_SECOND_ATTEMPT} points",
        "      - Wrong twice = the correct answer is shown",
        "4. After the quiz:",
        "      - See your total score and rank.",
        "      - Play again or exit.",
    ]
    return "\n".join(lines)


def enableHighDpi():
    """On Windows, stop display scaling from blurring the window."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # not Windows, or not supported: nothing to do


def loadCustomFont():
    """Load a .ttf from the assets folder for this program only (Windows)."""
    if FONT_FILE is None or sys.platform != "win32":
        return
    path = ASSETS / FONT_FILE
    if not path.exists():
        return
    try:
        import ctypes
        FR_PRIVATE = 0x10
        ctypes.windll.gdi32.AddFontResourceExW(str(path), FR_PRIVATE, 0)
    except Exception:
        pass


# The quiz itself. A class keeps the game state (score, question number, etc.)
class MathsQuiz:
    def __init__(self, root):
        self.root = root
        self.root.title("Math Quiz")
        self.root.resizable(False, False)

        if not PILLOW_AVAILABLE:
            print("Pillow is not installed, so images are disabled. "
                  "Run:  pip install pillow")

        # Work out the window size: shrink to fit the screen, never enlarge
        screenW = root.winfo_screenwidth()
        screenH = root.winfo_screenheight()
        self.scale = min(screenW / DESIGN_W,
                         (screenH - TASKBAR_ALLOWANCE) / DESIGN_H,
                         1)
        self.width = int(DESIGN_W * self.scale)
        self.height = int(DESIGN_H * self.scale)

        self.canvas = tk.Canvas(root, width=self.width, height=self.height,
                                highlightthickness=0, bg=FALLBACK_BG)
        self.canvas.pack()

        # Game state
        self.level = 1
        self.score = 0
        self.questionNumber = 1
        self.attempt = 1
        self.correctAnswer = 0
        self.acceptingInput = False

        # Things we create per screen (so they can be cleaned up)
        self.widgets = []
        self.bgItem = None
        self.loadingText = None
        self.titleItem = None
        self.questionItem = None
        self.scoreItem = None
        self.problemItem = None
        self.feedbackItem = None
        self.answerEntry = None
        self.submitButton = None

        # Scheduled animation jobs (cancelled whenever the screen changes)
        self.bgJob = None
        self.titleJob = None
        self.nextQuestionJob = None
        self.loadingJob = None

        # Loading screen: plain background with animated "Loading..." text.
        # loadBackground() refreshes the window after every frame it loads,
        # which is what keeps the dots moving while the images load.
        loadingStart = time.time()
        self.loadingText = self.drawText(DESIGN_W / 2 - 170, DESIGN_H / 2,
                                         "Loading", 70, anchor="w")
        self.animateLoadingText(0)
        self.keepAlive()

        # Images are kept on self, otherwise Python deletes them and they vanish
        # (each file is loaded once, even if several screens share it)
        loaded = {}
        self.backgrounds = {}
        for screen, filename in BACKGROUND_FILES.items():
            if filename not in loaded:
                loaded[filename] = self.loadBackground(ASSETS / filename)
            self.backgrounds[screen] = loaded[filename]

        # Don't let the loading screen vanish in a flash
        while time.time() - loadingStart < MIN_LOADING_SECONDS:
            self.keepAlive()
            time.sleep(0.01)

        # Enter submits the answer; Escape closes the program
        self.root.bind("<Return>", self.onEnterPressed)
        self.root.bind("<Escape>", lambda event: self.root.destroy())

        self.displayTitle()

    #scaling and drawing helpers
    def s(self, value):
        """Convert a 1920x1080 design coordinate to the real window size."""
        return int(value * self.scale)

    def fontSize(self, size):
        """Scale a font size given in 1920x1080 pixels.

        Tkinter treats negative font sizes as pixels (positive means points),
        which keeps text the same size relative to your artwork on any screen.
        """
        return -max(8, int(size * self.scale))

    def drawText(self, x, y, text, size, colour=TEXT_COLOUR, anchor="center", **options):
        """Draw text on the canvas (canvas text has a see-through background)."""
        return self.canvas.create_text(
            self.s(x), self.s(y), text=text, fill=colour, anchor=anchor,
            font=(FONT_NAME, self.fontSize(size), FONT_STYLE), **options
        )

    def addButton(self, text, command, x, y, width=14):
        """Place a styled button on the canvas, with a hover colour change."""
        button = tk.Button(
            self.canvas, text=text, command=command, width=width,
            font=(FONT_NAME, self.fontSize(42), FONT_STYLE),
            bg=BUTTON_BG, fg=BUTTON_FG,
            activebackground=BUTTON_HOVER, activeforeground=BUTTON_FG,
            bd=0, relief="flat", cursor="hand2",
        )
        button.bind("<Enter>", lambda event: button.config(bg=BUTTON_HOVER))
        button.bind("<Leave>", lambda event: button.config(bg=BUTTON_BG))
        self.canvas.create_window(self.s(x), self.s(y), window=button)
        self.widgets.append(button)
        return button

    #loading images 
    def keepAlive(self):
        """Let Tkinter redraw and run animations while we are busy loading."""
        try:
            self.root.update()
        except tk.TclError:
            sys.exit()  # the window was closed during loading

    def loadBackground(self, path):
        """Load a PNG or GIF as (frames, delays), scaled to the window.

        A still image gives one frame; an animated GIF gives several.
        Returns None if the file is missing or Pillow isn't installed.
        """
        if not PILLOW_AVAILABLE:
            return None
        if not path.exists():
            # Say so, otherwise a wrong file name just gives a plain background
            print(f"Warning: background image not found: {path}")
            return None

        image = Image.open(path)
        total = getattr(image, "n_frames", 1)
        # Very long GIFs eat memory, so keep every nth frame (and lengthen delays)
        stride = max(1, math.ceil(total / MAX_GIF_FRAMES))
        # Still images get the slower, sharper resize; animation uses the fast one
        method = Image.LANCZOS if total == 1 else Image.BILINEAR

        frames, delays = [], []
        for index in range(0, total, stride):
            image.seek(index)
            delay = max(MIN_FRAME_DELAY_MS, image.info.get("duration", 50) * stride)
            frame = image.convert("RGB").resize((self.width, self.height), method)
            frames.append(ImageTk.PhotoImage(frame))
            delays.append(delay)
            self.keepAlive()  # keeps the loading animation moving
        return frames, delays

    #screen management 
    def stopAnimations(self):
        """Cancel every running animation. Called whenever the screen changes."""
        for job in (self.bgJob, self.titleJob, self.nextQuestionJob, self.loadingJob):
            if job is not None:
                self.root.after_cancel(job)
        self.bgJob = self.titleJob = self.nextQuestionJob = self.loadingJob = None

    def showScreen(self, name):
        """Wipe the previous screen and draw this screen's background."""
        self.stopAnimations()
        self.canvas.delete("all")
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []
        self.acceptingInput = False

        background = self.backgrounds.get(name)
        if background is not None:
            frames, _ = background
            self.bgItem = self.canvas.create_image(0, 0, image=frames[0], anchor="nw")
            if len(frames) > 1:
                self.playBackground(background, 0)

    # animation 
    def playBackground(self, background, index):
        """Show one frame of the animated background, then schedule the next."""
        frames, delays = background
        self.canvas.itemconfig(self.bgItem, image=frames[index])
        nextIndex = (index + 1) % len(frames)
        self.bgJob = self.root.after(delays[index], self.playBackground,
                                     background, nextIndex)

    def animateLoadingText(self, step):
        """Cycle the dots after 'Loading': none, one, two, three, repeat."""
        self.canvas.itemconfig(self.loadingText, text="Loading" + "." * (step % 4))
        self.loadingJob = self.root.after(400, self.animateLoadingText, step + 1)

    def bobTitle(self, step):
        """Float the title text gently up and down using a sine wave."""
        offset = math.sin(step / 8) * self.s(TITLE_BOB_PIXELS)
        x, y = LAYOUT["title"]
        self.canvas.coords(self.titleItem, self.s(x), self.s(y) + offset)
        self.titleJob = self.root.after(30, self.bobTitle, step + 1)

    #screens 
    def displayTitle(self):
        """Title screen: background, floating title text, Start button."""
        self.showScreen("title")

        self.titleItem = self.drawText(*LAYOUT["title"], "Maths Quiz", 130)
        self.bobTitle(0)
        self.addButton("START", self.displayInstructions, *LAYOUT["startButton"])

    def displayInstructions(self):
        """Instructions screen."""
        self.showScreen("instructions")
        self.drawText(*LAYOUT["instructionsText"], buildInstructions(), 36,
                      anchor="nw", justify="left")
        self.addButton("CONTINUE", self.displayMenu, *LAYOUT["continueButton"])

    def displayMenu(self):
        """Show the difficulty level menu."""
        self.showScreen("menu")
        self.drawText(*LAYOUT["menuHeading"], "DIFFICULTY LEVEL", 80)

        for (level, (name, _, _)), position in zip(LEVELS.items(), LAYOUT["menuButtons"]):
            self.addButton(
                f"{level}. {name}",
                # level=level locks in the current value for each button
                lambda level=level: self.startQuiz(level),
                *position, width=16,
            )

    def startQuiz(self, level):
        """Reset the game state, build the quiz screen and ask question 1."""
        self.level = level
        self.score = 0
        self.questionNumber = 1
        self.attempt = 1

        self.showScreen("quiz")

        self.questionItem = self.drawText(*LAYOUT["questionCounter"], "", 40, QUIZ_TEXT_COLOUR)
        self.scoreItem = self.drawText(*LAYOUT["score"], "", 40, QUIZ_TEXT_COLOUR)
        self.problemItem = self.drawText(*LAYOUT["problem"], "", 110, QUIZ_TEXT_COLOUR)

        self.answerEntry = tk.Entry(
            self.canvas, font=(FONT_NAME, self.fontSize(56), FONT_STYLE), width=8,
            justify="center", bg="white", fg="#1b1b3a",
            insertbackground="#1b1b3a", relief="flat",
        )
        self.canvas.create_window(self.s(LAYOUT["answerBox"][0]),
                                  self.s(LAYOUT["answerBox"][1]),
                                  window=self.answerEntry)
        self.widgets.append(self.answerEntry)

        self.submitButton = self.addButton("SUBMIT", self.submitAnswer, *LAYOUT["submitButton"])
        self.feedbackItem = self.drawText(*LAYOUT["feedback"], "", 40, QUIZ_TEXT_COLOUR,
                                          width=self.s(1200), justify="center")

        self.displayProblem()

    def setFeedback(self, message, colour=QUIZ_TEXT_COLOUR):
        """Show a message under the answer box."""
        self.canvas.itemconfig(self.feedbackItem, text=message, fill=colour)

    def updateLabels(self):
        """Refresh the question counter and the score."""
        self.canvas.itemconfig(
            self.questionItem,
            text=f"Question {self.questionNumber} of {QUESTIONS_PER_QUIZ}")
        self.canvas.itemconfig(self.scoreItem, text=f"Score: {self.score}")

    def displayProblem(self):
        """Generate a new question, show it and get ready to accept an answer."""
        self.nextQuestionJob = None

        # All questions asked? Go to the results screen.
        if self.questionNumber > QUESTIONS_PER_QUIZ:
            self.displayResults()
            return

        num1 = randomInt(self.level)
        num2 = randomInt(self.level)
        operation = decideOperation()

        if operation == "+":
            self.correctAnswer = num1 + num2
        else:
            self.correctAnswer = num1 - num2  # may be negative, that's fine

        self.attempt = 1
        self.canvas.itemconfig(self.problemItem, text=f"{num1} {operation} {num2} =")
        self.updateLabels()
        self.setFeedback("")

        # Re-enable the controls (they are disabled while feedback is showing)
        self.answerEntry.config(state="normal")
        self.submitButton.config(state="normal")
        self.answerEntry.delete(0, tk.END)
        self.answerEntry.focus_set()
        self.acceptingInput = True

    def isCorrect(self, userAnswer):
        """Check the answer, update the score and show a suitable message.

        Returns True if the answer was right, otherwise False.
        """
        if userAnswer == self.correctAnswer:
            points = POINTS_FIRST_ATTEMPT if self.attempt == 1 else POINTS_SECOND_ATTEMPT
            self.score += points
            self.setFeedback(f"Correct! +{points} points", GOOD_COLOUR)
            return True

        if self.attempt == 1:
            self.setFeedback("Not quite. Have one more go!", WARN_COLOUR)
        else:
            self.setFeedback(f"Wrong again. The answer was {self.correctAnswer}.", BAD_COLOUR)
        return False

    def displayResults(self):
        """Show the final score out of 100, the rank, and the play-again option."""
        self.showScreen("results")

        rank = getRank(self.score)
        self.drawText(*LAYOUT["resultsScore"], f"Your score: {self.score} / {MAX_SCORE}", 90)
        self.drawText(*LAYOUT["resultsRank"], f"Rank: {rank}", 110)

        self.addButton("PLAY AGAIN", self.displayMenu, *LAYOUT["playAgainButton"])
        self.addButton("EXIT", self.root.destroy, *LAYOUT["exitButton"])

    #event handlers 
    def onEnterPressed(self, event):
        """Enter key does the same as clicking Submit (only during a quiz)."""
        if self.acceptingInput:
            self.submitAnswer()

    def submitAnswer(self):
        """Read the entry box, validate it and decide what happens next."""
        if not self.acceptingInput:
            return

        text = self.answerEntry.get().strip()
        try:
            userAnswer = int(text)
        except ValueError:
            # Not a whole number: warn them but don't use up an attempt
            self.setFeedback("Please enter a whole number (e.g. 12 or -5).", BAD_COLOUR)
            return

        correct = self.isCorrect(userAnswer)
        self.updateLabels()

        if correct or self.attempt == 2:
            # Question finished: lock the controls briefly, then move on
            self.acceptingInput = False
            self.answerEntry.config(state="disabled")
            self.submitButton.config(state="disabled")
            self.questionNumber += 1
            self.nextQuestionJob = self.root.after(FEEDBACK_DELAY_MS, self.displayProblem)
        else:
            # First attempt wrong: allow a second try at the same question
            self.attempt = 2
            self.answerEntry.delete(0, tk.END)
            self.answerEntry.focus_set()

# Program entry point
def main():
    enableHighDpi()
    loadCustomFont()
    root = tk.Tk()
    MathsQuiz(root)
    root.mainloop()


if __name__ == "__main__":
    main()