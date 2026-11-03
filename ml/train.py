# train.py
#
# Trains a model that reads a test's code and predicts how likely it is to
# be flaky, then measures how good it is and saves it to ml/model.pkl.
#
# The model:
#   1. TF-IDF turns each test into numbers: one number per word, bigger when
#      the word is common in this test but rare across all tests.
#   2. Logistic regression learns a weight for each word. Words like "sleep"
#      or "environ" push the score up; others push it down. The score is
#      turned into a probability between 0 and 1.
#
# How it's tested: the tests are split by PROJECT, so the model is always
# scored on projects it never saw during training. Splitting tests randomly
# instead would let it "cheat" by recognising projects, and the score would
# look much better than it really is (this script shows that too).
#
# Run it with:   .venv/bin/python ml/train.py

import csv
import os
import pickle
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.features import to_text  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "data", "dataset.csv")
MODEL_PATH = os.path.join(HERE, "model.pkl")
SEED = 0


def make_model():
    return make_pipeline(
        TfidfVectorizer(min_df=3, sublinear_tf=True),
        LogisticRegression(C=1, class_weight="balanced", solver="liblinear"),
    )


def found_in_top(y, scores, fraction):
    """If you only investigate the riskiest `fraction` of tests, what share
    of all the flaky tests do you find?"""
    top = np.argsort(-scores)[: int(len(scores) * fraction)]
    return y[top].sum() / y.sum()


def report(name, y, scores):
    print(f"  {name:28} AUC {roc_auc_score(y, scores):.3f}   "
          f"AP {average_precision_score(y, scores):.3f}   "
          f"flaky found in top 20%: {found_in_top(y, scores, 0.2):.0%}")


def main():
    csv.field_size_limit(sys.maxsize)
    with open(DATASET, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    texts = [to_text(r["code"], r["context"]) for r in rows]
    y = np.array([int(r["flaky"]) for r in rows])
    projects = np.array([r["project"] for r in rows])
    print(f"{len(rows)} tests from {len(set(projects))} projects, {y.mean():.0%} flaky\n")

    # 5-fold cross-validation, split by project: train on 80% of projects,
    # score the other 20%, and repeat 5 times so every test gets scored once.
    by_project = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = cross_val_predict(make_model(), texts, y, groups=projects,
                               cv=by_project, method="predict_proba")[:, 1]

    rng = np.random.default_rng(SEED)
    lengths = np.array([len(r["code"]) for r in rows])

    print("On projects the model never saw (the honest numbers):")
    report("random guessing", y, rng.random(len(y)))
    report("longer test = riskier", y, lengths)
    report("model", y, scores)

    leaky = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    leaky_scores = cross_val_predict(make_model(), texts, y, cv=leaky,
                                     method="predict_proba")[:, 1]
    print("\nSplitting randomly instead (looks better, but it's cheating):")
    report("model", y, leaky_scores)

    # Train the final model on everything and save it.
    model = make_model().fit(texts, y)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    words = np.array(model[0].get_feature_names_out())
    weights = model[1].coef_[0]
    print("\nWords that make a test look most flaky:")
    print("  " + ", ".join(words[np.argsort(-weights)[:15]]))
    print(f"\nSaved the model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
