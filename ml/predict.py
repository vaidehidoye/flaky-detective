# predict.py
#
# Loads the trained model and scores the tests in a file: a number from 0 to 1
# for how flaky each test looks, judged only by reading its code.
#
# The score is good for RANKING tests (higher = check it first), but it is not
# a true probability: the model was trained to pay extra attention to the
# rarer flaky tests, which pushes every score up.

import os
import pickle

from ml.features import tests_in_file, to_text

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")


def load_model():
    """Return the trained model, or None if it (or scikit-learn) isn't available.

    The detective works without the model, so this never crashes.
    """
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception:
        # No model file, scikit-learn not installed, or a different version
        # of scikit-learn that can't read this file. Carry on without it.
        return None


def risk_scores(model, path):
    """Return {test name: risk score from 0 to 1} for every test in a file."""
    with open(path, encoding="utf-8") as f:
        source = f.read()
    tests = tests_in_file(source)
    if not tests:
        return {}
    texts = [to_text(code, context) for _, code, context in tests]
    risks = model.predict_proba(texts)[:, 1]
    return {name: float(risk) for (name, _, _), risk in zip(tests, risks)}
