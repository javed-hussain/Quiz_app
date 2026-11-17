import json
import tempfile
import unittest
from pathlib import Path

from quiz_app import (
    QuestionBankError,
    calculate_score,
    load_question_bank,
    review_items,
    validate_question_bank,
)


VALID_QUESTION = {
    "question": "Pick one",
    "options": ["A", "B"],
    "answer": "A",
}


class QuestionBankTests(unittest.TestCase):
    def test_accepts_valid_bank(self):
        self.assertEqual(validate_question_bank([VALID_QUESTION]), [VALID_QUESTION])

    def test_rejects_empty_or_non_array_bank(self):
        for data in ([], {}, None):
            with self.subTest(data=data), self.assertRaises(QuestionBankError):
                validate_question_bank(data)

    def test_rejects_missing_or_blank_prompt(self):
        for prompt in (None, "  "):
            bad = {**VALID_QUESTION, "question": prompt}
            with self.subTest(prompt=prompt), self.assertRaises(QuestionBankError):
                validate_question_bank([bad])

    def test_rejects_unsuitable_options_and_duplicate_options(self):
        for options in (["A"], ["A", ""], ["A", "A"], "A, B"):
            bad = {**VALID_QUESTION, "options": options}
            with self.subTest(options=options), self.assertRaises(QuestionBankError):
                validate_question_bank([bad])

    def test_rejects_answer_that_does_not_match_option(self):
        bad = {**VALID_QUESTION, "answer": "a"}
        with self.assertRaisesRegex(QuestionBankError, "exactly match"):
            validate_question_bank([bad])

    def test_rejects_non_object_question(self):
        with self.assertRaisesRegex(QuestionBankError, "JSON object"):
            validate_question_bank(["question"])

    def test_loads_json_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "questions.json"
            path.write_text(json.dumps([VALID_QUESTION]), encoding="utf-8")
            self.assertEqual(load_question_bank(path), [VALID_QUESTION])

    def test_reports_malformed_json_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(QuestionBankError, "Invalid JSON"):
                load_question_bank(path)
            with self.assertRaisesRegex(QuestionBankError, "not found"):
                load_question_bank(Path(directory) / "missing.json")


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.questions = [VALID_QUESTION, {**VALID_QUESTION, "answer": "B"}]

    def test_score_counts_only_correct_answers(self):
        self.assertEqual(calculate_score(self.questions, ["A", None]), 1)

    def test_review_includes_wrong_and_unanswered(self):
        self.assertEqual(
            review_items(self.questions, ["B", None]),
            [(1, "B", "A"), (2, None, "B")],
        )

    def test_score_and_review_require_one_answer_slot_per_question(self):
        with self.assertRaises(ValueError):
            calculate_score(self.questions, ["A"])
        with self.assertRaises(ValueError):
            review_items(self.questions, [])


if __name__ == "__main__":
    unittest.main()
