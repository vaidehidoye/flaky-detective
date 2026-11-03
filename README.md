# 🕵️ Flaky Detective

A tool that figures out **why** a test is flaky.

## What's a flaky test?

A test is a small check that makes sure code works ("does 2 + 2 give 4?").
A **flaky** test sometimes passes and sometimes fails, even when nothing changed.
That usually happens because something hidden changes between runs:

- ⏰ **the clock**: it fails at certain times
- 🎲 **randomness**: some random values break it
- 🧍🧍 **order**: another test leaves a mess behind
- 🏃 **speed**: two things race, and sometimes the wrong one wins

Flaky Detective runs a test over and over, locks down one suspect at a time,
and reports which one is to blame.

## Try it

```
python3 detective.py
```

Example output:

```
test_good             passed 100  failed   0   ✅ reliable (always passes)
test_moody_clock      passed  76  failed  24   🎭 FLAKY (sometimes passes, sometimes fails)
test_moody_random     passed  92  failed   8   🎭 FLAKY (sometimes passes, sometimes fails)
```

## Files

| File | What it does |
|------|--------------|
| `moody_tests.py` | Example tests, some of them moody on purpose |
| `detective.py`   | Runs each test many times, then freezes suspects to find the culprit |

## Roadmap

- [x] Moody example tests
- [x] Detect *that* a test is flaky
- [x] Find out *why*: freeze randomness
- [x] Freeze the clock
- [ ] Shuffle test order
- [ ] Catch speed races
- [ ] Friendly report
