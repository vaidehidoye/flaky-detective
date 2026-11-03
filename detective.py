# detective.py
#
# Step 2 of the project: run every test many times and count how often
# it passes and fails. A test that does both is "flaky".
#
# Run it with:   python3 detective.py

import time

import moody_tests

RUNS = 100  # how many times to run each test


def find_tests(module):
    """Find every function in the module whose name starts with 'test_'."""
    tests = []
    for name in dir(module):
        if name.startswith("test_"):
            tests.append(getattr(module, name))
    return tests


def run_once(test):
    """Run a test one time. Return True if it passed, False if it failed."""
    try:
        test()
        return True
    except AssertionError:
        return False


def investigate(test):
    """Run a test RUNS times and count the results."""
    passes = 0
    fails = 0
    for _ in range(RUNS):
        if run_once(test):
            passes += 1
        else:
            fails += 1
        time.sleep(0.01)  # a tiny pause, so runs happen at different moments
    return passes, fails


def main():
    print(f"Running each test {RUNS} times...\n")
    for test in find_tests(moody_tests):
        passes, fails = investigate(test)

        if fails == 0:
            verdict = "✅ reliable (always passes)"
        elif passes == 0:
            verdict = "❌ broken (always fails)"
        else:
            verdict = "🎭 FLAKY (sometimes passes, sometimes fails)"

        print(f"{test.__name__:20}  passed {passes:3}  failed {fails:3}   {verdict}")


if __name__ == "__main__":
    main()
