# flaky-detective

![check](https://github.com/vaidehidoye/flaky-detective/actions/workflows/check.yml/badge.svg)

Finds out why a test is flaky, and uses a model trained on real flaky tests
to decide which tests to check first.

A flaky test is one that sometimes passes and sometimes fails without any code
changing. Most tools only tell you a test is flaky. This one tries to find the
cause, from four common ones:

- **randomness**: the test uses random values
- **time**: the test depends on the current time
- **order**: another test leaves shared data behind
- **threads**: the test races against a background thread

## Usage

Needs Python 3.9+. The detective itself has no dependencies; the model needs
scikit-learn.

```
pip install -r requirements.txt

python3 detective.py                          # run on the example tests
python3 detective.py fixed_tests.py           # same tests, fixed
python3 detective.py my_tests.py              # run on your own file
python3 detective.py my_tests.py --top 10     # only investigate the 10 riskiest
python3 detective.py my_tests.py --predict-only
```

It prints each flaky test, the cause, and a suggested fix. It exits with 1 if
it found flaky tests and 0 if not, so it can be used in CI.

## How it works

0. **Predict.** The model reads each test's code and gives it a risk score.
   Tests are investigated riskiest first. This only changes the order, unless
   you pass `--top`.
1. **Run alone.** Each test is run 100 times. If it both passes and fails, it's flaky.
2. **Find the cause.** One cause is disabled at a time and the test is run
   again. If it stops being flaky, that's the cause.
   - randomness: reset the random seed before each run
   - time: replace `time.time` with a function that returns a fixed value
   - threads: replace `Thread.start` so the thread runs to completion immediately
3. **Run together.** All tests are run in 50 random orders. If a test that
   passed on its own starts failing, the other tests are run one at a time
   before it to find which one breaks it.

The model is fast but often wrong; the experiments are slow but reliable. The
model decides where to look, the experiments decide what's true.

## The model

**Data.** [IDoFT](https://github.com/TestingResearchIllinois/idoft) lists
flaky tests found in open-source Python projects, but only by name.
`ml/build_dataset.py` downloads each test file from GitHub at the commit the
flaky test was found in and extracts every test from it. Tests listed in IDoFT
are labelled flaky; the other tests in the same files are labelled not flaky.
This gives 5,665 tests from 297 projects, 22% of them flaky.

**Features.** For each test, the words in its code (identifiers split on
`snake_case` and `camelCase`) plus the words in the code around it: the
file's imports, the fixtures it uses, and its class's `setUp`/`tearDown`.
See `ml/features.py`.

**Model.** TF-IDF and logistic regression (`ml/train.py`).

**Evaluation.** 5-fold cross-validation, split by project, so the model is
always scored on projects it has never seen:

| | AUC | Flaky tests found in the riskiest 20% |
|---|---|---|
| Random guessing | 0.50 | 20% |
| Longer tests are riskier | 0.57 | 25% |
| Model, test code only | 0.58 | 25% |
| **Model, test code + surrounding code** | **0.63** | **32%** |
| Model, random split instead of by project | 0.87 | 61% |

The last row is what you get if tests from the same project end up in both
training and testing. The model learns to recognise projects instead of
flakiness, and the score looks much better than it is.

**What didn't work.**
- Predicting the *cause* (order, nondeterministic, or self-polluting) from
  code. The model barely beat always guessing "order", which is 78% of the
  data. Causes that look identical in code need the experiments.
- Hand-written features (does the test call `sleep`, use threads, touch
  `os.environ`, ...). No improvement over the word features.
- Only keeping words used in at least 5 projects, to stop the model learning
  project-specific names. No improvement.
- Embeddings from a pretrained code model
  ([UniXcoder](https://huggingface.co/microsoft/unixcoder-base)) with logistic
  regression. Same AUC (0.63) for a 500 MB model, so the smaller one stays.

To rebuild the dataset and retrain:

```
python3 ml/build_dataset.py   # downloads ~500 files from GitHub, cached in ml/data/
python3 ml/train.py           # prints the evaluation, saves ml/model.pkl
```

## Files

- `detective.py`: the tool
- `moody_tests.py`: example tests, each flaky for a different reason
- `fixed_tests.py`: the same tests with the problems fixed
- `ml/features.py`: turns test code into model input
- `ml/build_dataset.py`: builds the training data from IDoFT
- `ml/train.py`: trains and evaluates the model
- `ml/predict.py`: loads the model and scores a file's tests
- `ml/model.pkl`: the trained model
- `.github/workflows/check.yml`: runs the tool on `fixed_tests.py` on every push

## Limitations

- Tests have to be functions named `test_*` in a file in the same folder.
- Only the four causes above are checked. Anything else is reported as unknown.
- The model's scores are for ranking only. They aren't calibrated
  probabilities.
- With `--top`, flaky tests the model scores low are never checked.
