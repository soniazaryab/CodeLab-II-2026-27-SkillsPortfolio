"""
Exercise 3 - Student Manager (extension version)

Everything in the basic version, plus:
    5. Sort the student records (ascending or descending)
    6. Add a student record
    7. Delete a student record
    8. Update a student record
Changes made by 6, 7 and 8 are saved back to studentMarks.txt.

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
RED = "#dc2626"              # delete button
RED_HOVER = "#b91c1c"
LIGHT = "#f1f5f9"            # toolbar and background
STRIPE = "#eef2f7"           # every second table row
WHITE = "#ffffff"
TEXT = "#1e293b"
ERROR = "#b91c1c"
SUCCESS = "#15803d"


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

def save_students(path, students):
    """Write all the students back to the file in the same format we read it."""
    with open(path, "w", encoding="utf-8") as file:
        file.write(f"{len(students)}\n")          # the first line is the number of students
        for student in students:
            marks = ",".join(str(mark) for mark in student.coursework_marks)
            file.write(f"{student.code},{student.name},{marks},{student.exam_mark}\n")
# AI-assisted (Claude): writes the list back to the file in the same format it is read in

def read_number(text, lowest, highest):
    """Turn text into a whole number between lowest and highest, or return None if it isn't one."""
    try:
        number = int(text)
    except ValueError:
        return None
    if lowest <= number <= highest:
        return number
    return None


# What the Sort menu offers: (name shown, the value to sort by)
SORT_OPTIONS = [("Name", lambda student: student.name.lower()),
                ("Student No", lambda student: student.code),
                ("Coursework", lambda student: student.coursework_total()),
                ("Exam Mark", lambda student: student.exam_mark),
                ("Overall %", lambda student: student.total())]

# The boxes in the Add / Update form: (key, label)
FORM_FIELDS = [("code", "Student No (1000-9999)"),
               ("name", "Name"),
               ("mark1", "Coursework 1 (/20)"),
               ("mark2", "Coursework 2 (/20)"),
               ("mark3", "Coursework 3 (/20)"),
               ("exam", "Exam (/100)")]


class StudentManager:
    def __init__(self, root, students, path):
        self.root = root
        self.students = students
        self.path = path
        self.form_mode = None          # "add" or "update" while the form is open
        self.student_being_updated = None

        root.title("Student Manager System")
        root.geometry("1250x700")
        root.minsize(1000, 560)
        root.configure(bg=LIGHT)

        self.build_header()
        self.build_search_bar()
        self.build_bottom_buttons()     # the bottom parts are added before the table
        self.build_summary()            # so that they keep their space when the window shrinks
        self.build_main_area()

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
        self.search_box = tk.Entry(inner, font=(FONT, 12), width=24, relief="solid", bd=1)
        self.search_box.pack(side="left", padx=(0, 8), ipady=4)
        self.search_box.bind("<Return>", lambda event: self.search())   # Enter also searches
        self.make_button(inner, "Search", self.search).pack(side="left", padx=4)
        self.make_button(inner, "View All Records", self.show_all,
                         SLATE, SLATE_HOVER).pack(side="left", padx=4)

# The Sort button opens a menu: pick a field, then ascending or descending
        sort_button = tk.Menubutton(inner, text="Sort Students By  ▾", bg=SLATE, fg=WHITE,
                                    activebackground=SLATE_HOVER, activeforeground=WHITE,
                                    font=(FONT, 11, "bold"), bd=0, padx=18, pady=7,
                                    cursor="hand2")
        sort_menu = tk.Menu(sort_button, tearoff=0, font=(FONT, 11))
        for name, key in SORT_OPTIONS:
            sub_menu = tk.Menu(sort_menu, tearoff=0, font=(FONT, 11))
            # name=name, key=key makes each menu item remember its own field
            sub_menu.add_command(label="Ascending",
                                 command=lambda name=name, key=key: self.sort(name, key, False))
            sub_menu.add_command(label="Descending",
                                 command=lambda name=name, key=key: self.sort(name, key, True))
            sort_menu.add_cascade(label=name, menu=sub_menu)
        sort_button.config(menu=sort_menu)
        sort_button.pack(side="left", padx=4)
# AI-assisted (Claude): the Sort menu is built with a loop, and name=name, key=key makes each menu item remember its own field.

    def build_bottom_buttons(self):
        bar = tk.Frame(self.root, bg=LIGHT, pady=12)
        bar.pack(side="bottom", fill="x")
        inner = tk.Frame(bar, bg=LIGHT)
        inner.pack()
        self.make_button(inner, "Add Student", self.open_add_form).pack(side="left", padx=6)
        self.make_button(inner, "Update Student", self.open_update_form).pack(side="left", padx=6)
        self.make_button(inner, "Delete Student", self.delete_student,
                         RED, RED_HOVER).pack(side="left", padx=6)
        self.make_button(inner, "Highest Score", self.show_highest,
                         SLATE, SLATE_HOVER).pack(side="left", padx=(24, 6))
        self.make_button(inner, "Lowest Score", self.show_lowest,
                         SLATE, SLATE_HOVER).pack(side="left", padx=6)

    def build_summary(self):
        self.summary = tk.Label(self.root, text="", bg=LIGHT, fg=TEXT,
                                font=(FONT, 12, "bold"), pady=8)
        self.summary.pack(side="bottom", fill="x")

    def build_main_area(self):
        """The table on the left and the Add / Update form on the right."""
        main = tk.Frame(self.root, bg=LIGHT)
        main.pack(fill="both", expand=True, padx=12)
        self.build_form(main)         # the form is created now but only shown when needed
        self.build_table(main)

    def build_table(self, parent):
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

        frame = tk.Frame(parent, bg=WHITE)
        frame.pack(side="left", fill="both", expand=True)

        # (column id, heading, width, alignment)
        columns = [("code", "Student No", 100, "center"),
                   ("name", "Name", 220, "w"),
                   ("coursework", "Coursework (/60)", 140, "center"),
                   ("exam", "Exam (/100)", 110, "center"),
                   ("percent", "Overall %", 100, "center"),
                   ("grade", "Grade", 70, "center")]

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

    def build_form(self, parent):
        """The panel used for both adding and updating a student."""
        self.form = tk.Frame(parent, bg=WHITE, padx=20, pady=16, width=340)
        self.form.pack_propagate(False)       # keep the panel at its width

        self.form_title = tk.Label(self.form, text="", bg=WHITE, fg=NAVY,
                                   font=(FONT, 16, "bold"))
        self.form_title.pack(pady=(0, 12))

        self.entries = {}                     # key -> the Entry box
        for key, label in FORM_FIELDS:
            tk.Label(self.form, text=label, bg=WHITE, fg=TEXT, font=(FONT, 10),
                     anchor="w").pack(fill="x")
            entry = tk.Entry(self.form, font=(FONT, 12), relief="solid", bd=1)
            entry.pack(fill="x", pady=(2, 9), ipady=3)
            self.entries[key] = entry

        self.form_message = tk.Label(self.form, text="", bg=WHITE, fg=ERROR,
                                     font=(FONT, 10), wraplength=290, justify="left")
        self.form_message.pack(fill="x", pady=(0, 6))

        buttons = tk.Frame(self.form, bg=WHITE)
        buttons.pack()
        self.form_button = self.make_button(buttons, "", self.submit_form)
        self.form_button.pack(side="left", padx=4)
        self.make_button(buttons, "Cancel", self.close_form,
                         SLATE, SLATE_HOVER).pack(side="left", padx=4)

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
            # the student number is used as the row's id, so we can find the student again
            self.table.insert("", "end", iid=str(student.code), values=row, tags=(tag,))

    def set_summary(self, message, colour=TEXT):
        self.summary.config(text=message, fg=colour)

    def get_selected_student(self):
        """Return the student whose row is selected in the table (or None)."""
        selection = self.table.selection()
        if len(selection) == 0:
            return None
        code = int(selection[0])
        for student in self.students:
            if student.code == code:
                return student
        return None

    # ----- menu options 1 to 4 -----
    def show_all(self):
        """Option 1: every student, then the class size and average percentage."""
        self.search_box.delete(0, tk.END)
        self.show_table(self.students)
        if len(self.students) == 0:
            self.set_summary("There are no students in the class.")
            return
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
        if len(self.students) == 0:
            return
        highest = max(student.total() for student in self.students)
        # a list, because two students could have the same total
        best = [student for student in self.students if student.total() == highest]
        self.show_table(best)
        self.set_summary(f"Highest total score: {highest} out of {TOTAL_MAX}")

    def show_lowest(self):
        """Option 4: the student with the lowest total score."""
        if len(self.students) == 0:
            return
        lowest = min(student.total() for student in self.students)
        worst = [student for student in self.students if student.total() == lowest]
        self.show_table(worst)
        self.set_summary(f"Lowest total score: {lowest} out of {TOTAL_MAX}")

    # ----- option 5: sort -----
    def sort(self, field_name, key, descending):
        """Show the students sorted by the chosen field."""
        self.search_box.delete(0, tk.END)
        sorted_students = sorted(self.students, key=key, reverse=descending)
        self.show_table(sorted_students)
        order = "descending" if descending else "ascending"
        self.set_summary(f"Students sorted by {field_name} ({order})")

    # ----- options 6 and 8: the Add / Update form -----
    def open_form(self, mode, student=None):
        """Show the form on the right, empty for adding or filled in for updating."""
        self.form_mode = mode
        self.student_being_updated = student
        for entry in self.entries.values():
            entry.delete(0, tk.END)

        if mode == "add":
            self.form_title.config(text="Add Student")
            self.form_button.config(text="Add")
        else:
            self.form_title.config(text="Update Student")
            self.form_button.config(text="Save Changes")
            self.entries["code"].insert(0, student.code)
            self.entries["name"].insert(0, student.name)
            for number in range(3):
                self.entries[f"mark{number + 1}"].insert(0, student.coursework_marks[number])
            self.entries["exam"].insert(0, student.exam_mark)

        self.form_message.config(text="")
        self.form.pack(side="right", fill="y", padx=(12, 0))
        self.entries["code"].focus_set()

    def close_form(self):
        self.form.pack_forget()
        self.form_mode = None
        self.student_being_updated = None

    def open_add_form(self):
        self.open_form("add")

    def open_update_form(self):
        student = self.get_selected_student()
        if student is None:
            self.set_summary("Search for the student, click their row, then press Update Student.",
                             ERROR)
            return
        self.open_form("update", student)

    def read_form(self):
        """Check what was typed in the form. Returns (Student, "") or (None, error message)."""
        values = {key: entry.get().strip() for key, entry in self.entries.items()}

        code = read_number(values["code"], 1000, 9999)
        if code is None:
            return None, "The student number must be a whole number from 1000 to 9999."
        for other in self.students:
            # another student must not already have this number
            if other.code == code and other is not self.student_being_updated:
                return None, f"Student number {code} is already used by {other.name}."

        name = values["name"]
        if name == "":
            return None, "Please enter the student's name."
        if "," in name:
            return None, "The name can't contain a comma (the file uses commas to separate data)."

        marks = []
        for number in range(1, 4):
            mark = read_number(values[f"mark{number}"], 0, 20)
            if mark is None:
                return None, f"Coursework {number} must be a whole number from 0 to 20."
            marks.append(mark)

        exam = read_number(values["exam"], 0, EXAM_MAX)
        if exam is None:
            return None, "The exam mark must be a whole number from 0 to 100."

        return Student(code, name, marks, exam), ""

    def submit_form(self):
        """The Add / Save Changes button: check the form, change the list, save the file."""
        student, error = self.read_form()
        if student is None:
            self.form_message.config(text=error)
            return

        if self.form_mode == "add":
            self.students.append(student)
            message = f"Added {student.name}."
        else:
            # replace the old record with the new one, in the same place in the list
            position = self.students.index(self.student_being_updated)
            self.students[position] = student
            message = f"Updated {student.name}."

        if not self.save():
            return
        self.close_form()
        self.show_all()
        self.table.selection_set(str(student.code))     # highlight the student we just changed
        self.table.see(str(student.code))
        self.set_summary(message, SUCCESS)

    # ----- option 7: delete -----
    def delete_student(self):
        student = self.get_selected_student()
        if student is None:
            self.set_summary("Search for the student, click their row, then press Delete Student.",
                             ERROR)
            return
        question = (f"Delete {student.name} (student number {student.code})?"
                    "\n\nThis can't be undone.")
        if not messagebox.askyesno("Delete student", question):
            return

        self.students.remove(student)
        if not self.save():
            return
        self.close_form()
        self.show_all()
        self.set_summary(f"Deleted {student.name}.", SUCCESS)

    # ----- saving -----
    def save(self):
        """Write the students to the file. Returns True if it worked."""
        try:
            save_students(self.path, self.students)
            return True
        except OSError as error:
            messagebox.showerror("Could not save", f"The file could not be saved:\n{error}")
            return False


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

    StudentManager(root, students, path)
    root.deiconify()           # show the window now that everything is ready
    root.mainloop()


if __name__ == "__main__":
    main()