# fixed_tests.py
#
# The same tests as moody_tests.py, but with every flakiness bug FIXED,
# following the advice in the detective's case file.
#
# Check them with:   python3 detective.py fixed_tests.py
# The detective should find nothing wrong.

import random
import threading
import time


def add(a, b):
    """The tiny program we're testing: it adds two numbers."""
    return a + b


shopping_cart = []


def test_good():
    assert add(2, 2) == 4


def test_fixed_random():
    # FIX: give the test its own dice with a fixed seed, so it sees the
    # same "random" number every single run.
    dice = random.Random(1)
    lucky_number = dice.randint(1, 100)
    assert lucky_number <= 90, f"got unlucky number {lucky_number}"


def is_late_enough(moment):
    """The logic we really want to check, with the time passed IN."""
    return moment % 1 >= 0.3


def test_fixed_clock():
    # FIX: don't ask the real clock. Pass in exact moments we choose,
    # so the answer is the same every run.
    assert is_late_enough(1_700_000_000.5)
    assert not is_late_enough(1_700_000_000.1)


def test_fixed_add_to_cart():
    # FIX: clean up after yourself, so no mess is left for the next test.
    shopping_cart.append("apple")
    assert "apple" in shopping_cart
    shopping_cart.clear()


def test_cart_starts_empty():
    assert len(shopping_cart) == 0, f"cart already has {shopping_cart}"


def test_fixed_speed():
    # FIX: instead of guessing how long to wait, join() waits until the
    # helper is truly finished, however long that takes.
    results = []

    def slow_helper():
        time.sleep(0.002)
        results.append("done")

    helper = threading.Thread(target=slow_helper)
    helper.start()
    helper.join()
    assert results == ["done"]
