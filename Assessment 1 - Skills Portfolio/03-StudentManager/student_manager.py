"""
Exercise 3 - Student Manager

Loads the student marks from studentMarks.txt and lets the user:
    1. View all student records (with the class size and average percentage)
    2. View an individual student record (search by name or student number)
    3. Show the student with the highest total score
    4. Show the student with the lowest total score

Each line of studentMarks.txt looks like this:
    8439,Jake Hobbs,10,11,10,43
which is: student number, name, three coursework marks (out of 20), exam mark (out of 100).
The first line of the file is the number of students.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk

# ----- settings -----
DATA_FILE = "studentMarks.txt"
FOLDER = os.path.dirname(os.path.abspath(__file__))

COURSEWORK_MAX = 60                      # three marks, each out of 20
EXAM_MAX = 100
TOTAL_MAX = COURSEWORK_MAX + EXAM_MAX    # 160 marks available in total

FONT = "Segoe UI"
NAVY = "#1e3a5f"             # header and table headings
BLUE = "#2563eb"             # main buttons
BLUE_HOVER = "#1d4ed8"
SLATE = "#475569"            # second buttons
SLATE_HOVER = "#334155"
LIGHT = "#f1f5f9"            # toolbar and background
STRIPE = "#eef2f7"           # every second table row
WHITE = "#ffffff"
TEXT = "#1e293b"
ERROR = "#b91c1c"


class Student:
    """One student's record, with the calculations for their results."""

    def __init__(self, code, name, coursework_marks, exam_mark):
        self.code = code
        self.name = name
        self.coursework_marks = coursework_marks      # a list of the three marks
        self.exam_mark = exam_mark

    def coursework_total(self):
        return sum(self.coursework_marks)

    def total(self):
        """Coursework plus exam, out of 160."""
        return self.coursework_total() + self.exam_mark

    def percentage(self):
        return self.total() / TOTAL_MAX * 100

    def grade(self):
        percent = self.percentage()
        if percent >= 70:
            return "A"
        elif percent >= 60:
            return "B"
        elif percent >= 50:
            return "C"
        elif percent >= 40:
            return "D"
        else:
            return "F"


def find_data_file():
    """Look for studentMarks.txt in a few folders and return its path."""
    folders = [FOLDER,
               os.path.join(FOLDER, "resources"),
               os.path.join(os.path.dirname(FOLDER), "resources"),
               os.path.dirname(FOLDER)]
    for folder in folders:
        path = os.path.join(folder, DATA_FILE)
        if os.path.exists(path):
            return path
    return None


def load_students(path):
    """Read the file and return a list of Student objects."""
    with open(path, encoding="utf-8-sig", errors="replace") as file:
        lines = file.read().splitlines()

    expected = int(lines[0])          # the first line is the number of students
    students = []
    for number, line in enumerate(lines[1:], start=2):
        if line.strip() == "":
            continue                  # skip blank lines
        parts = line.split(",")
        try:
            code = int(parts[0])
            name = parts[1].strip()
            marks = [int(part) for part in parts[2:5]]
            exam = int(parts[5])
        except (ValueError, IndexError):
            print(f"Skipped line {number} because it isn't in the right format: {line}")
            continue
        students.append(Student(code, name, marks, exam))

    if len(students) != expected:
        print(f"Warning: the file says {expected} students but {len(students)} were loaded.")
    return students


class StudentManager:
    def __init__(self, root, students):
        self.root = root
        self.students = students

        root.title("Student Manager System")
        root.geometry("1100x650")
        root.minsize(900, 500)
        root.configure(bg=LIGHT)

        self.build_header()
        self.build_search_bar()
        self.build_bottom_buttons()     # the bottom parts are added before the table
        self.build_summary()            # so that they keep their space when the window shrinks
        self.build_table()

        self.show_all()

    # ----- building the window -----
    def make_button(self, parent, text, command, colour=BLUE, hover=BLUE_HOVER):
        """Make a flat button that changes colour when the mouse is over it."""
        button = tk.Button(parent, text=text, command=command, bg=colour, fg=WHITE,
                           activebackground=hover, activeforeground=WHITE,
                           font=(FONT, 11, "bold"), bd=0, padx=18, pady=7, cursor="hand2")
        button.bind("<Enter>", lambda event: button.config(bg=hover))
        button.bind("<Leave>", lambda event: button.config(bg=colour))
        return button

    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY)
        header.pack(fill="x")
        tk.Label(header, text="Student Manager System", bg=NAVY, fg=WHITE,
                 font=(FONT, 22, "bold"), pady=16).pack()

    def build_search_bar(self):
        bar = tk.Frame(self.root, bg=LIGHT, pady=14)
        bar.pack(fill="x")
        inner = tk.Frame(bar, bg=LIGHT)
        inner.pack()          # packing with no side puts it in the middle

        tk.Label(inner, text="Search by name or student number:", bg=LIGHT, fg=TEXT,
                 font=(FONT, 11)).pack(side="left", padx=(0, 8))
        self.search_box = tk.Entry(inner, font=(FONT, 12), width=26, relief="solid", bd=1)
        self.search_box.pack(side="left", padx=(0, 8), ipady=4)
        self.search_box.bind("<Return>", lambda event: self.search())   # Enter also searches
        self.make_button(inner, "Search", self.search).pack(side="left", padx=4)
        self.make_button(inner, "View All Records", self.show_all,
                         SLATE, SLATE_HOVER).pack(side="left", padx=4)

    def build_bottom_buttons(self):
        bar = tk.Frame(self.root, bg=LIGHT, pady=12)
        bar.pack(side="bottom", fill="x")
        inner = tk.Frame(bar, bg=LIGHT)
        inner.pack()
        self.make_button(inner, "Highest Score", self.show_highest).pack(side="left", padx=6)
        self.make_button(inner, "Lowest Score", self.show_lowest).pack(side="left", padx=6)

    def build_summary(self):
        self.summary = tk.Label(self.root, text="", bg=LIGHT, fg=TEXT,
                                font=(FONT, 12, "bold"), pady=8)
        self.summary.pack(side="bottom", fill="x")

    def build_table(self):
        # Style the table (the "clam" theme lets us change the heading colours)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=(FONT, 11), rowheight=32, background=WHITE,
                        fieldbackground=WHITE, foreground=TEXT, borderwidth=0)
        style.configure("Treeview.Heading", font=(FONT, 11, "bold"), background=NAVY,
                        foreground=WHITE, relief="flat", padding=8)
        style.map("Treeview.Heading", background=[("active", NAVY)])
        style.map("Treeview", background=[("selected", "#bfdbfe")],
                  foreground=[("selected", TEXT)])

        frame = tk.Frame(self.root, bg=WHITE)
        frame.pack(fill="both", expand=True, padx=12)

        # (column id, heading, width, alignment)
        columns = [("code", "Student No", 110, "center"),
                   ("name", "Name", 260, "w"),
                   ("coursework", "Coursework (/60)", 150, "center"),
                   ("exam", "Exam (/100)", 120, "center"),
                   ("percent", "Overall %", 110, "center"),
                   ("grade", "Grade", 80, "center")]

        self.table = ttk.Treeview(frame, columns=[column[0] for column in columns],
                                  show="headings", selectmode="browse")
        for column_id, heading, width, alignment in columns:
            self.table.heading(column_id, text=heading)
            self.table.column(column_id, width=width, anchor=alignment)
        self.table.tag_configure("stripe", background=STRIPE)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
# AI-assisted (Claude): styles the ttk Treeview table (the clam theme lets the heading colours be changed)

    # ----- showing results -----
    def show_table(self, students):
        """Put these students in the table, in the same format every time."""
        self.table.delete(*self.table.get_children())      # clear the old rows
        for position, student in enumerate(students):
            row = (student.code,
                   student.name,
                   student.coursework_total(),
                   student.exam_mark,
                   f"{student.percentage():.2f}%",
                   student.grade())
            # every second row gets the stripe colour
            tag = "stripe" if position % 2 == 1 else ""
            self.table.insert("", "end", values=row, tags=(tag,))

    def set_summary(self, message, colour=TEXT):
        self.summary.config(text=message, fg=colour)

    # ----- the four menu options -----
    def show_all(self):
        """Option 1: every student, then the class size and average percentage."""
        self.search_box.delete(0, tk.END)
        self.show_table(self.students)
        total_percent = sum(student.percentage() for student in self.students)
        average = total_percent / len(self.students)
        self.set_summary(f"Students in the class: {len(self.students)}"
                         f"          Average percentage mark: {average:.2f}%")

    def search(self):
        """Option 2: find a student by student number or by (part of) their name."""
        text = self.search_box.get().strip()
        if text == "":
            self.set_summary("Type a name or student number to search.", ERROR)
            return

        matches = []
        for student in self.students:
            if text == str(student.code) or text.lower() in student.name.lower():
                matches.append(student)

        if len(matches) == 0:
            self.show_table([])
            self.set_summary(f'No student found for "{text}".', ERROR)
        else:
            self.show_table(matches)
            self.set_summary(f'Students found for "{text}": {len(matches)}')

    def show_highest(self):
        """Option 3: the student with the highest total score."""
        highest = max(student.total() for student in self.students)
        # a list, because two students could have the same total
        best = [student for student in self.students if student.total() == highest]
        self.show_table(best)
        self.set_summary(f"Highest total score: {highest} out of {TOTAL_MAX}")

    def show_lowest(self):
        """Option 4: the student with the lowest total score."""
        lowest = min(student.total() for student in self.students)
        worst = [student for student in self.students if student.total() == lowest]
        self.show_table(worst)
        self.set_summary(f"Lowest total score: {lowest} out of {TOTAL_MAX}")


def main():
    root = tk.Tk()
    root.withdraw()            # hide the empty window while we load the file

    path = find_data_file()
    if path is None:
        messagebox.showerror("File not found", f"Could not find {DATA_FILE}.")
        return
    try:
        students = load_students(path)
    except (ValueError, OSError) as error:
        messagebox.showerror("Problem reading the file", str(error))
        return
    if len(students) == 0:
        messagebox.showerror("No students", f"No student records found in {DATA_FILE}.")
        return

    StudentManager(root, students)
    root.deiconify()           # show the window now that everything is ready
    root.mainloop()


if __name__ == "__main__":
    main()