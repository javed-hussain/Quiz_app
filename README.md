# Revision Quiz App

A local desktop application for practising multiple-choice revision questions.
It uses Python and Tkinter and has no third-party dependencies.

## Run the app

From this directory, run:

```sh
python3 quiz_app.py
```

The app loads `questions.json` beside the Python file. To use another bank,
pass its path:

```sh
python3 quiz_app.py /path/to/questions.json
```

The bank is read-only from the app's perspective. It must be a non-empty JSON
array. Each question must have a `question` string, an `options` array with at
least two unique strings, and an `answer` string that exactly matches one of
the options. Invalid banks are rejected with a clear error before a quiz starts.

Unanswered questions are allowed when finishing; they count as incorrect and
appear in the answer review with the correct answer.

## Run tests

```sh
python3 -m unittest discover -s tests -v
```

## Included sample bank

`questions.json` contains five sample questions. Edit or replace that file to
create a different quiz, following the format above.
