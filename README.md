# flaky-detective

![check](https://github.com/vaidehidoye/flaky-detective/actions/workflows/check.yml/badge.svg)

Finds out why a test is flaky.

A flaky test is one that sometimes passes and sometimes fails without any code
changing. Most tools only tell you a test is flaky. This one tries to find the
cause, from four common ones:

- **randomness**: the test uses random values
- **time**: the test depends on the current time
- **order**: another test leaves shared data behind
- **threads**: the test races against a background thread

## Usage

Needs Python 3.9+. No dependencies.

```
python3 detective.py                  # run on the example tests
python3 detective.py fixed_tests.py   # same tests, fixed
python3 detective.py my_tests.py      # run on your own file
```

It prints each flaky test, the cause, and a suggested fix. It exits with 1 if
it found flaky tests and 0 if not, so it can be used in CI.

## How it works

1. Each test is run 100 times on its own. If it both passes and fails, it's flaky.
2. For each flaky test, one cause is disabled at a time and the test is run
   again. If it stops being flaky, that's the cause.
   - randomness: reset the random seed before each run
   - time: replace `time.time` with a function that returns a fixed value
   - threads: replace `Thread.start` so the thread runs to completion immediately
3. All tests are then run together in 50 random orders. If a test that passed
   on its own starts failing, the other tests are run one at a time before it
   to find which one breaks it.

## Files

- `detective.py`: the tool
- `moody_tests.py`: example tests, each flaky for a different reason
- `fixed_tests.py`: the same tests with the problems fixed
- `.github/workflows/check.yml`: runs the tool on `fixed_tests.py` on every push

## Limitations

- Tests have to be functions named `test_*` in a file in the same folder.
- Only the four causes above are checked. Anything else is reported as unknown.
