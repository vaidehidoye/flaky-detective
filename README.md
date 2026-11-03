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
PHASE 1: running each test alone, 100 times

test_moody_clock          passed  66  failed  34   🎭 FLAKY, investigating...
    with 🎲 randomness frozen: passed  61  failed  39
    with ⏰ clock frozen: passed 100  failed   0
    🎯 Culprit: ⏰ clock

test_moody_random         passed  88  failed  12   🎭 FLAKY, investigating...
    with 🎲 randomness frozen: passed 100  failed   0
    🎯 Culprit: 🎲 randomness

PHASE 2: running all tests together in 50 shuffled orders

test_cart_starts_empty    passed alone, but failed in 25/50 shuffled orders
    🎯 Culprit: 🧍🧍 order. It fails whenever test_add_to_cart runs before it
```

## How it works

1. **Alone:** run each test 100 times. If it both passes and fails, it's flaky.
   Freeze one suspect at a time (randomness, then the clock). The suspect whose
   freezing makes the moodiness stop is the culprit.
2. **Together:** run every test in 50 shuffled orders, starting fresh each time.
   A test that was fine alone but fails here is being tripped up by another
   test. Try each other test right before it to find which one leaves the mess.

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
- [x] Shuffle test order
- [ ] Catch speed races
- [ ] Friendly report
