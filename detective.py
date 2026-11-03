# detective.py
#
# Step 2: run every test many times and count how often it passes and fails.
#         A test that does both is "flaky".
# Step 3: for each flaky test, lock down one suspect at a time.
#         If the test stops being moody, that suspect is the culprit.
#
# Run it with:   python3 detective.py

import random
import time

import moody_tests

RUNS = 100  # how many times to run each test


# ---------------------------------------------------------------------------
# Suspects
#
# Each suspect has a "freeze" function. It runs right before every test run
# and locks that one source of moodiness in place.
# ---------------------------------------------------------------------------

def freeze_randomness():
    # Computers don't make truly random numbers. They follow a recipe that
    # starts from a number called a "seed". Same seed -> same "random"
    # numbers every time. Resetting the seed before each run means the test
    # sees exactly the same random numbers on every run.
    random.seed(42)


SUSPECTS = {
    "🎲 randomness": freeze_randomness,
}


# ---------------------------------------------------------------------------
# Running tests
# ---------------------------------------------------------------------------

def find_tests(module):
    """Find every function in the module whose name starts with 'test_'."""
    tests = []
    for name in dir(module):
        if name.startswith("test_"):
            tests.append(getattr(module, name))
    return tests


def run_once(test, freeze=None):
    """Run a test one time. Return True if it passed, False if it failed.

    If a freeze function is given, call it first to lock down a suspect.
    """
    if freeze is not None:
        freeze()
    try:
        test()
        return True
    except AssertionError:
        return False


def investigate(test, freeze=None):
    """Run a test RUNS times and count the results."""
    passes = 0
    fails = 0
    for _ in range(RUNS):
        if run_once(test, freeze):
            passes += 1
        else:
            fails += 1
        time.sleep(0.01)  # a tiny pause, so runs happen at different moments
    return passes, fails


def is_flaky(passes, fails):
    """Flaky means it did BOTH: passed at least once and failed at least once."""
    return passes > 0 and fails > 0


def find_culprit(test):
    """Try freezing each suspect. Return the first one that cures the moodiness."""
    for suspect_name, freeze in SUSPECTS.items():
        passes, fails = investigate(test, freeze)
        print(f"    with {suspect_name} frozen: passed {passes:3}  failed {fails:3}")
        if not is_flaky(passes, fails):
            return suspect_name
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Running each test {RUNS} times...\n")
    for test in find_tests(moody_tests):
        passes, fails = investigate(test)

        if not is_flaky(passes, fails):
            verdict = "✅ reliable" if fails == 0 else "❌ broken (always fails)"
            print(f"{test.__name__:20}  passed {passes:3}  failed {fails:3}   {verdict}\n")
            continue

        print(f"{test.__name__:20}  passed {passes:3}  failed {fails:3}   🎭 FLAKY, investigating...")
        culprit = find_culprit(test)
        if culprit:
            print(f"    🎯 Culprit: {culprit}\n")
        else:
            print("    🤷 No suspect explains it (yet!)\n")


if __name__ == "__main__":
    main()
