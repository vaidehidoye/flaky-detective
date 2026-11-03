# 🕵️ Flaky Detective

![Detective check](https://github.com/vaidehidoye/flaky-detective/actions/workflows/check.yml/badge.svg)

A tool that figures out **why** a test is flaky, and tells you how to fix it.

## What's a flaky test?

A test is a small check that makes sure code works ("does 2 + 2 give 4?").
A **flaky** test sometimes passes and sometimes fails, even when nothing changed.
That usually happens because something hidden changes between runs:

- 🎲 **randomness**: some random values break it
- ⏰ **the clock**: it fails at certain times
- 🧍🧍 **order**: another test leaves a mess behind
- 🏃 **speed**: two things race, and sometimes the wrong one wins

Most tools can only tell you *that* a test is flaky. Flaky Detective runs
experiments to find out *why*.

## Try it

No installs needed, just Python 3.9 or newer.

```
python3 detective.py                    # investigate the example moody tests
python3 detective.py fixed_tests.py     # the same tests, fixed: all reliable
python3 detective.py your_tests.py      # investigate your own tests file
```

Example case file:

```
======================================================================
📋 CASE FILE for moody_tests.py
======================================================================
4 of 6 tests are flaky:

  test_moody_clock         ⏰ clock
                           → fix: don't depend on the real time; pass the time in or fake it

  test_moody_random        🎲 randomness
                           → fix: set a fixed seed in the test, e.g. random.seed(1)

  test_moody_speed         🏃 speed
                           → fix: wait for helpers properly with .join() instead of sleeping

  test_cart_starts_empty   🧍🧍 order
                           → fix: test_add_to_cart leaves a mess; make it clean up after itself
```

The detective exits with code `0` if everything is reliable and `1` if it
found flakiness, so you can use it in automatic checks (see `.github/workflows/check.yml`).

## How it works

The core idea is a **controlled experiment**: change one thing, see if the problem goes away.

**Phase 1, each test alone.** Run each test 100 times. If it both passes and
fails, it's flaky. Then freeze one suspect at a time and run it 100 more times:

| Suspect | How it's frozen |
|---|---|
| 🎲 randomness | reset the random seed to 42 before every run |
| ⏰ clock | swap `time.time` for a fake clock stuck at one moment |
| 🏃 speed | swap `Thread.start` so helper threads finish their job right away |

The suspect whose freezing makes the flakiness disappear is the culprit.

**Phase 2, tests together.** Run every test in 50 shuffled orders, starting
fresh each time. A test that was fine alone but fails here is being tripped up
by another test. Try each other test right before it to find which one leaves
the mess.

## Files

| File | What it does |
|------|--------------|
| `detective.py`     | The detective |
| `moody_tests.py`   | Example tests, each moody for a different reason |
| `fixed_tests.py`   | The same tests with every bug fixed |
| `.github/workflows/check.yml` | Runs the detective on GitHub after every push |

## Limitations

- Tests must be plain functions named `test_...` in a file in this folder.
- It only knows four suspects. A test that's flaky for another reason
  (such as network or files on disk) is reported as "unknown".
- Freezing speed only works for tests that use Python's `threading`.
