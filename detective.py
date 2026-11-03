# detective.py
#
# Phase 1: investigate each test ALONE.
#   Run it many times and count passes and fails. A test that does both is
#   "flaky". For each flaky test, lock down one suspect at a time. If the test
#   stops being moody, that suspect is the culprit.
#
# Phase 2: investigate tests TOGETHER.
#   Some tests only misbehave when another test ran before them and left a
#   mess. Run the whole set of tests in shuffled orders to catch those, then
#   test pairs to find out exactly who made the mess.
#
# Run it with:   python3 detective.py

import importlib
import random
import time

import moody_tests

RUNS = 100        # Phase 1: how many times to run each test on its own
SHUFFLES = 50     # Phase 2: how many shuffled orders of the whole set to try

# The detective's own private dice for shuffling. Kept separate from the
# `random` the tests use, so that freezing randomness doesn't freeze our shuffles.
shuffler = random.Random()


# ---------------------------------------------------------------------------
# Suspects
#
# Each suspect has two functions:
#   freeze   runs right before a test run and locks that suspect in place
#   unfreeze runs right after, and puts everything back to normal
# ---------------------------------------------------------------------------

def freeze_randomness():
    # Computers don't make truly random numbers. They follow a recipe that
    # starts from a number called a "seed". Same seed -> same "random"
    # numbers every time. Resetting the seed before each run means the test
    # sees exactly the same random numbers on every run.
    random.seed(42)


def unfreeze_randomness():
    # Calling seed() with no number picks a fresh, unpredictable seed.
    random.seed()


# We can't stop real time, but we can trick the test. In Python a function
# is just a value, like a number, so we can swap time.time for our own fake
# function that always reports the same moment.
REAL_TIME = time.time
FROZEN_MOMENT = 1_700_000_000.5  # a fixed moment, halfway through a second


def fake_time():
    return FROZEN_MOMENT


def freeze_clock():
    time.time = fake_time


def unfreeze_clock():
    time.time = REAL_TIME  # put the real clock back


SUSPECTS = {
    "🎲 randomness": (freeze_randomness, unfreeze_randomness),
    "⏰ clock": (freeze_clock, unfreeze_clock),
}


# ---------------------------------------------------------------------------
# Running tests
# ---------------------------------------------------------------------------

def fresh_start():
    """Reload the tests file from scratch, so everything shared (like the
    shopping cart) is brand new and empty. Like tidying the room."""
    importlib.reload(moody_tests)


def find_test_names():
    """Find every function in the tests file whose name starts with 'test_'."""
    return [name for name in dir(moody_tests) if name.startswith("test_")]


def run_once(name, suspect=None):
    """Run a test one time. Return True if it passed, False if it failed.

    If a suspect is given, freeze it before the test and unfreeze it after.
    """
    # We look the test up by name every time, because fresh_start() replaces
    # the old test functions with brand-new copies.
    test = getattr(moody_tests, name)
    if suspect is not None:
        freeze, unfreeze = suspect
        freeze()
    try:
        test()
        return True
    except AssertionError:
        return False
    finally:
        # "finally" runs no matter what, pass or fail, so the suspect
        # is always unfrozen and can't leak into the next run.
        if suspect is not None:
            unfreeze()


def is_flaky(passes, fails):
    """Flaky means it did BOTH: passed at least once and failed at least once."""
    return passes > 0 and fails > 0


# ---------------------------------------------------------------------------
# Phase 1: each test alone
# ---------------------------------------------------------------------------

def investigate_alone(name, suspect=None):
    """Run one test RUNS times on its own and count the results."""
    fresh_start()
    passes = 0
    fails = 0
    for _ in range(RUNS):
        if run_once(name, suspect):
            passes += 1
        else:
            fails += 1
        time.sleep(0.01)  # a tiny pause, so runs happen at different moments
    return passes, fails


def find_culprit(name):
    """Try freezing each suspect. Return the first one that cures the moodiness."""
    for suspect_name, suspect in SUSPECTS.items():
        passes, fails = investigate_alone(name, suspect)
        print(f"    with {suspect_name} frozen: passed {passes:3}  failed {fails:3}")
        if not is_flaky(passes, fails):
            return suspect_name
    return None


def phase_one(names):
    """Investigate every test alone. Return the names of the reliable ones."""
    print(f"PHASE 1: running each test alone, {RUNS} times\n")
    reliable = []
    for name in names:
        passes, fails = investigate_alone(name)

        if not is_flaky(passes, fails):
            verdict = "✅ reliable" if fails == 0 else "❌ broken (always fails)"
            print(f"{name:24}  passed {passes:3}  failed {fails:3}   {verdict}\n")
            if fails == 0:
                reliable.append(name)
            continue

        print(f"{name:24}  passed {passes:3}  failed {fails:3}   🎭 FLAKY, investigating...")
        culprit = find_culprit(name)
        if culprit:
            print(f"    🎯 Culprit: {culprit}\n")
        else:
            print("    🤷 No suspect explains it (yet!)\n")
    return reliable


# ---------------------------------------------------------------------------
# Phase 2: tests together, in shuffled orders
# ---------------------------------------------------------------------------

def find_mess_maker(victim, others):
    """Try each other test right before the victim, starting fresh each time.
    Whoever makes the victim fail is the one leaving the mess."""
    for other in others:
        fresh_start()
        run_once(other)
        if not run_once(victim):
            return other
    return None


def phase_two(names, reliable):
    """Shuffle all tests together and look for reliable tests that start failing."""
    print(f"PHASE 2: running all tests together in {SHUFFLES} shuffled orders\n")

    failures = {name: 0 for name in reliable}
    for _ in range(SHUFFLES):
        order = names[:]           # copy the list...
        shuffler.shuffle(order)    # ...and mix it up
        fresh_start()
        for name in order:
            if not run_once(name) and name in failures:
                failures[name] += 1

    found_any = False
    for victim, count in failures.items():
        if count == 0:
            continue
        found_any = True
        print(f"{victim:24}  passed alone, but failed in {count}/{SHUFFLES} shuffled orders")
        others = [name for name in names if name != victim]
        mess_maker = find_mess_maker(victim, others)
        if mess_maker:
            print(f"    🎯 Culprit: 🧍🧍 order. It fails whenever {mess_maker} runs before it\n")
        else:
            print("    🤷 Couldn't pin it on a single other test\n")

    if not found_any:
        print("No order problems found ✅\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    names = find_test_names()
    reliable = phase_one(names)
    phase_two(names, reliable)


if __name__ == "__main__":
    main()
