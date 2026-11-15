"""
Exercise 1 - Maths Quiz

A quiz of 10 addition and subtraction questions with three difficulty levels.
Screens: title -> instructions -> difficulty menu -> quiz -> results.

Scoring: 10 points for a correct answer on the first try,
         5 points for a correct answer on the second try,
         0 points if both tries are wrong.

The backgrounds go in an "assets" folder next to this file:
    bg_title.gif    title screen 
    bg_main.gif     instructions, menu and results
    bg_quiz.png     quiz screen
    fonts/PirataOne-Regular.ttf    font for the title and results screens
    fonts/Aldrich-Regular.ttf      font for everything else
"""

import math
import os
import random
import time
import tkinter as tk
from tkinter import font

from PIL import Image, ImageTk       # loads and resizes the background pictures

# ----- settings -----
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
QUESTIONS = 10
FEEDBACK_DELAY = 1200       # milliseconds the feedback stays on screen
LOADING_SECONDS = 1.5       # the loading screen stays at least this long
MAX_FRAMES = 30             # long GIFs are thinned out to this many frames (saves memory)

# Fonts. The files are in assets/fonts and the names are what the fonts are called
# once loaded. If a font can't be loaded, BACKUP_FONT is used instead.
FONT_FOLDER = os.path.join(ASSETS, "fonts")
TITLE_FONT_FILE = "PirataOne-Regular.ttf"
TITLE_FONT = "Pirata One"         # used for the title and results screens
TEXT_FONT_FILE = "Aldrich-Regular.ttf"
TEXT_FONT = "Aldrich"             # used for everything else
BACKUP_FONT = "Comic Sans MS"
WHITE = "#ffffff"
NAVY = "#0f1b44"            # dark text for the quiz screen
GREEN = "#15803d"
ORANGE = "#b45309"
RED = "#b91c1c"
BUTTON_COLOUR = "#5b21d9"
BUTTON_HOVER_COLOUR = "#7c3aed"
LOADING_BACKGROUND = "#0f0a2a"

# My pictures are 1920 x 1080, so every position below is for that size.
# Each position is (x, y), the centre of the item.
LOADING_POS = (790, 540)            # left edge of the word "Loading"
TITLE_POS = (960, 300)
START_POS = (960, 640)
INSTRUCTIONS_POS = (480, 190)       # top-left corner of the instructions text
CONTINUE_POS = (960, 960)
MENU_HEADING_POS = (960, 250)
MENU_POSITIONS = [(960, 450), (960, 600), (960, 750)]
QUESTION_NUMBER_POS = (960, 250)
SCORE_POS = (540, 250)
PROBLEM_POS = (960, 400)
ANSWER_POS = (960, 530)
SUBMIT_POS = (960, 640)
FEEDBACK_POS = (960, 730)
RESULT_SCORE_POS = (960, 400)
RESULT_RANK_POS = (960, 540)
PLAY_AGAIN_POS = (700, 760)
EXIT_POS = (1220, 760)

# Difficulty level: (name, smallest number, largest number)
LEVELS = {
    1: ("Easy", 1, 9),
    2: ("Moderate", 10, 99),
    3: ("Advanced", 1000, 9999),
}

INSTRUCTIONS = """Instructions:
1. Choose a difficulty level:
      - Easy: numbers from 1 to 9
      - Moderate: numbers from 10 to 99
      - Advanced: numbers from 1000 to 9999
2. Answer the questions:
      - You get 10 problems.
      - Type your answer and press Submit (or Enter).
3. Scoring:
      - Correct on the first try = 10 points
      - Correct on the second try = 5 points
      - Wrong twice = the correct answer is shown
4. After the quiz:
      - See your total score and rank.
      - Play again or exit."""


def stopWindowsBlurring():
    """On Windows, stop display scaling from making the window look blurry."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass     # not Windows, so there is nothing to do


def loadFonts():
    """On Windows, make the font files in assets/fonts available to this program only."""
    try:
        import ctypes
        for filename in (TITLE_FONT_FILE, TEXT_FONT_FILE):
            path = os.path.join(FONT_FOLDER, filename)
            ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)   # 0x10 = just this program
    except Exception:
        pass     # not Windows, so the fonts must be installed on the computer


def randomInt(level):
    """Return a random number for the chosen difficulty level."""
    name, smallest, largest = LEVELS[level]
    return random.randint(smallest, largest)


def decideOperation():
    """Randomly choose + or -."""
    return random.choice(["+", "-"])


def getRank(score):
    """Turn a score out of 100 into a grade."""
    if score > 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


class MathsQuiz:
    def __init__(self, root):
        self.root = root
        root.title("Maths Quiz")
        root.configure(bg="black")
        root.minsize(640, 360)
        root.bind("<Escape>", lambda event: root.destroy())

        # Use the backup font for any font that couldn't be loaded
        installed = font.families()
        self.titleFont = TITLE_FONT if TITLE_FONT in installed else BACKUP_FONT
        self.textFont = TEXT_FONT if TEXT_FONT in installed else BACKUP_FONT

        screenWidth = root.winfo_screenwidth()
        screenHeight = root.winfo_screenheight()
        scale = min(1, screenWidth / 1920, (screenHeight - 100) / 1080)
        root.geometry(f"{int(1920 * scale)}x{int(1080 * scale)}")

        # The canvas holds the picture. place() keeps it in the middle, so if the
        # window is not the same shape as the picture the extra space shows as black borders.
        self.canvas = tk.Canvas(root, highlightthickness=0, bg=LOADING_BACKGROUND)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")
        self.setSize(scale)

        # Every screen gets a new number. Animations remember the number of the
        # screen they started on, and stop when it no longer matches.
        self.screenNumber = 0

        # The game's information
        self.level = 1
        self.score = 0
        self.questionNumber = 1
        self.attempt = 1
        self.correctAnswer = 0

        # What is on the quiz screen, kept so it can be drawn again after a resize
        self.counterString = ""
        self.problemString = ""
        self.feedbackString = ""
        self.feedbackColour = NAVY

        self.screen = "loading"        # which screen is showing
        self.resizeTimer = None        # remembers the waiting resize (see onResize)

        # Loading screen: a plain background with the word "Loading" and moving dots.
        startTime = time.time()
        self.loadingText = self.write(LOADING_POS, "Loading", 70, anchor="w")
        self.animateLoading(0)

        # The three backgrounds, saved on self so Python doesn't delete them.
        # Each one is a list of frames and a delay: a GIF has many, a PNG has one.
        self.loadPictures(True)

        # Keep the loading screen up for a minimum time so it doesn't flash past
        while time.time() - startTime < LOADING_SECONDS:
            self.root.update()
            time.sleep(0.01)

        self.displayTitle()

        # From now on, whenever the window changes size (maximise, restore or dragging
        # the edge) onResize runs. This is bound last so it doesn't run during setup.
        root.bind("<Configure>", self.onResize)

    # ----- window size -----
    def setSize(self, scale):
        """Use this scale for everything: the canvas, the pictures and the text."""
        self.scale = scale
        self.width = int(1920 * scale)
        self.height = int(1080 * scale)
        self.canvas.config(width=self.width, height=self.height)

    def loadPictures(self, showProgress):
        """Load the three backgrounds. They are saved on self so Python doesn't delete them."""
        self.titlePicture = self.loadPicture("bg_title.gif", showProgress)
        self.mainPicture = self.loadPicture("bg_main.gif", showProgress)
        self.quizPicture = self.loadPicture("bg_quiz.png", showProgress)

    def onResize(self, event):
        """The window changed size. Wait until the changing stops, then fit the picture."""
        if event.widget is not self.root:       # ignore events from things inside the window
            return
        if self.resizeTimer is not None:
            self.root.after_cancel(self.resizeTimer)
        # Dragging an edge fires this many times a second, so we wait 300 ms of calm
        self.resizeTimer = self.root.after(300, self.fitToWindow)

    def fitToWindow(self):
        """Make the picture as big as the window allows, then draw the screen again."""
        self.resizeTimer = None
        scale = min(self.root.winfo_width() / 1920, self.root.winfo_height() / 1080, 1)
        if abs(scale - self.scale) < 0.01 or self.screen == "loading":
            return                              # the picture already fits
        self.screenNumber += 1                  # stops the animations of the old pictures
        # Let go of the old pictures first, so they don't use memory at the same time as the new ones
        self.titlePicture = self.mainPicture = self.quizPicture = None
        self.setSize(scale)
        self.loadPictures(False)
        self.redraw()

    def redraw(self):
        """Draw the current screen again at the new size."""
        if self.screen == "title":
            self.displayTitle()
        elif self.screen == "instructions":
            self.displayInstructions()
        elif self.screen == "menu":
            self.displayMenu()
        elif self.screen == "quiz":
            self.redrawQuiz()
        else:
            self.displayResults()

    # ----- helpers -----
    def write(self, position, text, size, colour=WHITE, title=False, **options):
        """Write text on the canvas. Position and size are for the 1920 x 1080 design.

        title=True uses the title font, otherwise the normal text font.
        """
        x, y = position
        fontName = self.titleFont if title else self.textFont
        return self.canvas.create_text(
            x * self.scale, y * self.scale, text=text, fill=colour,
            font=(fontName, -int(size * self.scale), "bold"),   # minus = size in pixels
            **options)

    def addButton(self, position, text, command, width=14, title=False):
        """Put a button on the canvas. It changes colour when the mouse is over it."""
        x, y = position
        fontName = self.titleFont if title else self.textFont
        button = tk.Button(
            self.canvas, text=text, command=command, width=width,
            font=(fontName, -int(42 * self.scale), "bold"),
            bg=BUTTON_COLOUR, fg=WHITE, activebackground=BUTTON_HOVER_COLOUR,
            activeforeground=WHITE, bd=0, cursor="hand2")
        button.bind("<Enter>", lambda event: button.config(bg=BUTTON_HOVER_COLOUR))
        button.bind("<Leave>", lambda event: button.config(bg=BUTTON_COLOUR))
        self.canvas.create_window(x * self.scale, y * self.scale, window=button)
        return button

    # ----- pictures and animation -----
    def loadPicture(self, filename, showProgress=False):
        """Load a PNG or GIF, resized to fit the window. Returns (frames, delay)."""
        path = os.path.join(ASSETS, filename)
        if not os.path.exists(path):
            print("Warning: picture not found:", path)
            return None

        image = Image.open(path)
        total = getattr(image, "n_frames", 1)          # how many frames the file has
        step = max(1, total // MAX_FRAMES)             # use every 'step'th frame
        delay = max(20, image.info.get("duration", 50) * step)   # milliseconds per frame
        # A still picture can use the slower, sharper resize. Frames of a GIF use the quick one.
        method = Image.LANCZOS if total == 1 else Image.BILINEAR

        frames = []
        for number in range(0, total, step):
            image.seek(number)
            frame = image.convert("RGB").resize((self.width, self.height), method)
            frames.append(ImageTk.PhotoImage(frame))
            if showProgress:
                self.root.update()      # keeps the loading dots moving while we load
        return frames, delay

    def playBackground(self, frames, delay, number, screen):
        """Show one frame of an animated background, then schedule the next one."""
        if screen != self.screenNumber:     # the screen has changed, so stop
            return
        self.canvas.itemconfig(self.backgroundItem, image=frames[number])
        nextNumber = (number + 1) % len(frames)     # back to 0 after the last frame
        self.root.after(delay, self.playBackground, frames, delay, nextNumber, screen)

    def animateLoading(self, step):
        """Add one more dot to 'Loading' every 0.4 seconds (none, 1, 2, 3, repeat)."""
        if self.screenNumber != 0:          # the loading screen is finished
            return
        self.canvas.itemconfig(self.loadingText, text="Loading" + "." * (step % 4))
        self.root.after(400, self.animateLoading, step + 1)

    def floatTitle(self, step, screen):
        """Move the title up and down using a sine wave."""
        if screen != self.screenNumber:
            return
        x, y = TITLE_POS
        offset = math.sin(step / 8) * 14 * self.scale     
        self.canvas.coords(self.titleText, x * self.scale, y * self.scale + offset)
        self.root.after(30, self.floatTitle, step + 1, screen)

    def newScreen(self, name, picture):
        """Clear the old screen and draw a new background."""
        self.screen = name
        self.screenNumber += 1          # this stops the animations of the old screen
        for widget in self.canvas.winfo_children():
            widget.destroy()            # removes the old buttons and entry box
        self.canvas.delete("all")

        if picture is not None:
            frames, delay = picture
            self.backgroundItem = self.canvas.create_image(0, 0, image=frames[0], anchor="nw")
            if len(frames) > 1:         # a GIF with several frames, so play it
                self.playBackground(frames, delay, 0, self.screenNumber)

    # ----- screens -----
    def displayTitle(self):
        self.newScreen("title", self.titlePicture)
        self.titleText = self.write(TITLE_POS, "Maths Quiz", 170, title=True)
        self.floatTitle(0, self.screenNumber)
        self.addButton(START_POS, "START", self.displayInstructions, title=True)

    def displayInstructions(self):
        self.newScreen("instructions", self.mainPicture)
        self.write(INSTRUCTIONS_POS, INSTRUCTIONS, 36, anchor="nw", justify="left")
        self.addButton(CONTINUE_POS, "CONTINUE", self.displayMenu)

    def displayMenu(self):
        """The difficulty menu: one button for each level."""
        self.newScreen("menu", self.mainPicture)
        self.write(MENU_HEADING_POS, "DIFFICULTY LEVEL", 110, title=True)
        for level in LEVELS:
            name = LEVELS[level][0]
            # level=level makes each button remember its own level number
            self.addButton(MENU_POSITIONS[level - 1], f"{level}. {name}",
                           lambda level=level: self.startQuiz(level), width=16)

    def startQuiz(self, level):
        """Reset the score, build the quiz screen and ask the first question."""
        self.level = level
        self.score = 0
        self.questionNumber = 1
        self.counterString = ""
        self.problemString = ""
        self.feedbackString = ""
        self.feedbackColour = NAVY

        self.drawQuizScreen()
        self.displayProblem()

    def drawQuizScreen(self):
        """Draw the quiz screen with the question, score and message that are stored."""
        self.newScreen("quiz", self.quizPicture)
        self.questionText = self.write(QUESTION_NUMBER_POS, self.counterString, 40, NAVY)
        self.scoreText = self.write(SCORE_POS, f"Score: {self.score}", 40, NAVY)
        self.problemText = self.write(PROBLEM_POS, self.problemString, 110, NAVY)
        self.feedbackText = self.write(FEEDBACK_POS, self.feedbackString, 40,
                                       self.feedbackColour)

        # The box the player types their answer into
        self.answerEntry = tk.Entry(
            self.canvas, font=(self.textFont, -int(56 * self.scale), "bold"),
            width=8, justify="center")
        self.canvas.create_window(ANSWER_POS[0] * self.scale,
                                  ANSWER_POS[1] * self.scale, window=self.answerEntry)
        self.answerEntry.bind("<Return>", lambda event: self.submitAnswer())

        self.submitButton = self.addButton(SUBMIT_POS, "SUBMIT", self.submitAnswer)

    def redrawQuiz(self):
        """Draw the quiz screen again after a resize, keeping what the player typed."""
        typed = self.answerEntry.get()
        state = str(self.answerEntry.cget("state"))     # "disabled" while feedback shows
        self.drawQuizScreen()
        self.answerEntry.insert(0, typed)
        self.answerEntry.config(state=state)
        self.submitButton.config(state=state)
        if state == "normal":
            self.answerEntry.focus_set()

    def showFeedback(self, message, colour=NAVY):
        """Show a message under the answer box (and remember it for redrawing)."""
        self.feedbackString = message
        self.feedbackColour = colour
        self.canvas.itemconfig(self.feedbackText, text=message, fill=colour)

    # ----- the quiz -----
    def displayProblem(self):
        """Make a new question and show it."""
        # After the last question, show the results instead
        if self.questionNumber > QUESTIONS:
            self.displayResults()
            return

        number1 = randomInt(self.level)
        number2 = randomInt(self.level)
        operation = decideOperation()
        if operation == "+":
            self.correctAnswer = number1 + number2
        else:
            self.correctAnswer = number1 - number2

        self.attempt = 1
        self.problemString = f"{number1} {operation} {number2} ="
        self.counterString = f"Question {self.questionNumber} of {QUESTIONS}"
        self.canvas.itemconfig(self.problemText, text=self.problemString)
        self.canvas.itemconfig(self.questionText, text=self.counterString)
        self.canvas.itemconfig(self.scoreText, text=f"Score: {self.score}")
        self.showFeedback("")

        # Turn the entry box and button back on (they are off while feedback shows)
        self.answerEntry.config(state="normal")
        self.submitButton.config(state="normal")
        self.answerEntry.delete(0, tk.END)
        self.answerEntry.focus_set()

    def isCorrect(self, userAnswer):
        """Check the answer, change the score and show a message. Returns True or False."""
        if userAnswer == self.correctAnswer:
            if self.attempt == 1:
                points = 10
            else:
                points = 5
            self.score += points
            self.showFeedback(f"Correct! +{points} points", GREEN)
            return True

        if self.attempt == 1:
            self.showFeedback("Not quite. Have one more go!", ORANGE)
        else:
            self.showFeedback(f"Wrong again. The answer was {self.correctAnswer}.", RED)
        return False

    def submitAnswer(self):
        """Runs when the player presses Submit or Enter."""
        try:
            userAnswer = int(self.answerEntry.get())
        except ValueError:
            # Not a whole number, so show a message and don't use up a try
            self.showFeedback("Please enter a whole number (e.g. 12 or -5).", RED)
            return

        correct = self.isCorrect(userAnswer)
        self.canvas.itemconfig(self.scoreText, text=f"Score: {self.score}")

        if correct or self.attempt == 2:
            # This question is finished. Switch off the controls for a moment
            # so the player can read the message, then show the next question.
            self.answerEntry.config(state="disabled")
            self.submitButton.config(state="disabled")
            self.questionNumber += 1
            self.root.after(FEEDBACK_DELAY, self.displayProblem)
        else:
            # Wrong the first time, so they get a second go at the same question
            self.attempt = 2
            self.answerEntry.delete(0, tk.END)

    def displayResults(self):
        self.newScreen("results", self.mainPicture)
        self.write(RESULT_SCORE_POS, f"Your score: {self.score} / 100", 110, title=True)
        self.write(RESULT_RANK_POS, f"Rank: {getRank(self.score)}", 140, title=True)
        self.addButton(PLAY_AGAIN_POS, "PLAY AGAIN", self.displayMenu, title=True)
        self.addButton(EXIT_POS, "EXIT", self.root.destroy, title=True)


def main():
    stopWindowsBlurring()      # must be done before the window is created
    loadFonts()                # so is this
    root = tk.Tk()
    MathsQuiz(root)
    root.mainloop()


if __name__ == "__main__":
    main()