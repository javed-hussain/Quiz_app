"""A small, local multiple-choice revision quiz built with Tkinter."""

from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any


DEFAULT_QUESTION_PATH = Path(__file__).with_name("questions.json")


class QuestionBankError(ValueError):
    """Raised when a question bank cannot be used for a quiz."""


def validate_question_bank(data: Any) -> list[dict[str, Any]]:
    """Validate and return a normalized list of questions."""
    if not isinstance(data, list) or not data:
        raise QuestionBankError("The question bank must be a non-empty JSON array.")

    validated: list[dict[str, Any]] = []
    for number, question in enumerate(data, start=1):
        prefix = f"Question {number}"
        if not isinstance(question, dict):
            raise QuestionBankError(f"{prefix} must be a JSON object.")
        prompt = question.get("question")
        options = question.get("options")
        answer = question.get("answer")
        if not isinstance(prompt, str) or not prompt.strip():
            raise QuestionBankError(f"{prefix} needs a non-empty 'question' string.")
        if (not isinstance(options, list) or len(options) < 2
                or any(not isinstance(option, str) or not option.strip() for option in options)):
            raise QuestionBankError(f"{prefix} needs at least two non-empty string options.")
        if len(set(options)) != len(options):
            raise QuestionBankError(f"{prefix} has duplicate options.")
        if not isinstance(answer, str) or answer not in options:
            raise QuestionBankError(f"{prefix} 'answer' must exactly match one of its options.")
        validated.append({"question": prompt, "options": list(options), "answer": answer})
    return validated


def load_question_bank(path: str | Path) -> list[dict[str, Any]]:
    """Read and validate questions from a UTF-8 JSON file."""
    bank_path = Path(path)
    try:
        with bank_path.open("r", encoding="utf-8") as bank_file:
            data = json.load(bank_file)
    except FileNotFoundError as exc:
        raise QuestionBankError(f"Question bank not found: {bank_path}") from exc
    except json.JSONDecodeError as exc:
        raise QuestionBankError(
            f"Invalid JSON in {bank_path} (line {exc.lineno}, column {exc.colno})."
        ) from exc
    except OSError as exc:
        raise QuestionBankError(f"Could not read question bank {bank_path}: {exc}") from exc
    return validate_question_bank(data)


def calculate_score(questions: list[dict[str, Any]], answers: list[str | None]) -> int:
    """Return the number of correct responses; missing answers are incorrect."""
    if len(questions) != len(answers):
        raise ValueError("There must be exactly one response slot per question.")
    return sum(answer == question["answer"] for question, answer in zip(questions, answers))


def review_items(
    questions: list[dict[str, Any]], answers: list[str | None]
) -> list[tuple[int, str | None, str]]:
    """Return (1-based number, submitted answer, correct answer) for misses."""
    if len(questions) != len(answers):
        raise ValueError("There must be exactly one response slot per question.")
    return [
        (index, answer, question["answer"])
        for index, (question, answer) in enumerate(zip(questions, answers), start=1)
        if answer != question["answer"]
    ]


class QuizApp:
    def __init__(self, root: tk.Tk, questions: list[dict[str, Any]]) -> None:
        self.root = root
        self.questions = questions
        self.answers: list[str | None] = [None] * len(questions)
        self.current_index = 0
        self.finished = False
        self.root.title("Revision Quiz")
        self.root.minsize(520, 380)

        self.main = ttk.Frame(root, padding=24)
        self.main.pack(fill="both", expand=True)
        self.progress = ttk.Label(self.main, font=("TkDefaultFont", 10))
        self.progress.pack(anchor="w", pady=(0, 12))
        self.prompt = ttk.Label(self.main, font=("TkDefaultFont", 16, "bold"),
                                wraplength=460, justify="left")
        self.prompt.pack(anchor="w", fill="x", pady=(0, 20))
        self.choice = tk.StringVar(value="")
        self.options_frame = ttk.Frame(self.main)
        self.options_frame.pack(anchor="w", fill="x")
        self.navigation = ttk.Frame(self.main)
        self.navigation.pack(side="bottom", fill="x", pady=(24, 0))
        self.back_button = ttk.Button(self.navigation, text="← Back", command=self.go_back)
        self.back_button.pack(side="left")
        self.finish_button = ttk.Button(self.navigation, text="Finish quiz", command=self.finish)
        self.finish_button.pack(side="right")
        self.next_button = ttk.Button(self.navigation, text="Next →", command=self.go_next)
        self.next_button.pack(side="right", padx=(0, 8))
        self.render_question()

    def save_choice(self) -> None:
        self.answers[self.current_index] = self.choice.get() or None

    def render_question(self) -> None:
        question = self.questions[self.current_index]
        self.progress.configure(text=f"Question {self.current_index + 1} of {len(self.questions)}")
        self.prompt.configure(text=question["question"])
        self.choice.set(self.answers[self.current_index] or "")
        for child in self.options_frame.winfo_children():
            child.destroy()
        for option in question["options"]:
            ttk.Radiobutton(self.options_frame, text=option, value=option,
                            variable=self.choice, command=self.save_choice).pack(
                                anchor="w", fill="x", pady=5)
        self.back_button.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_button.configure(
            state="normal" if self.current_index < len(self.questions) - 1 else "disabled"
        )

    def go_back(self) -> None:
        self.save_choice()
        if self.current_index > 0:
            self.current_index -= 1
            self.render_question()

    def go_next(self) -> None:
        self.save_choice()
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.render_question()

    def finish(self) -> None:
        self.save_choice()
        self.finished = True
        score = calculate_score(self.questions, self.answers)
        for child in self.main.winfo_children():
            child.destroy()
        ttk.Label(self.main, text="Quiz complete", font=("TkDefaultFont", 20, "bold")).pack(
            anchor="w", pady=(0, 8)
        )
        ttk.Label(self.main, text=f"Your score: {score} / {len(self.questions)}",
                  font=("TkDefaultFont", 14)).pack(anchor="w", pady=(0, 18))
        ttk.Label(self.main, text="Review incorrect and unanswered questions:",
                  font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(0, 8))
        items = review_items(self.questions, self.answers)
        if not items:
            ttk.Label(self.main, text="All answers are correct.", wraplength=460).pack(
                anchor="w", pady=4
            )
        else:
            review = tk.Text(self.main, height=min(14, max(5, len(items) * 3)),
                             wrap="word", relief="flat", background=self.root.cget("bg"))
            review.pack(fill="both", expand=True)
            for index, submitted, correct in items:
                status = "Unanswered" if submitted is None else f"Your answer: {submitted}"
                review.insert("end", f"{index}. {self.questions[index - 1]['question']}\n")
                review.insert("end", f"   {status}\n   Correct answer: {correct}\n\n")
            review.configure(state="disabled")
        ttk.Button(self.main, text="Restart quiz", command=self.restart).pack(
            anchor="e", pady=(14, 0)
        )

    def restart(self) -> None:
        self.answers = [None] * len(self.questions)
        self.current_index = 0
        self.finished = False
        self.main.destroy()
        self.__init__(self.root, self.questions)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_QUESTION_PATH
    try:
        questions = load_question_bank(path)
    except QuestionBankError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Question bank error", str(exc), parent=root)
        root.destroy()
        return 1
    root = tk.Tk()
    QuizApp(root, questions)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
