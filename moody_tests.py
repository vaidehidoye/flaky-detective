# moody_tests.py
#
# These are the "suspects" for our detective to investigate.
# A test is just a function. If it finishes normally, it PASSED.
# If an `assert` line is false, Python raises an error and the test FAILED.

import random
import threading
import time


def add(a, b):
    """The tiny program we're testing: it adds two numbers."""
    return a + b


# A shopping cart that ALL tests share. Sharing things between tests is
# how one test can leave a mess for another.
shopping_cart = []


def test_good():
    # A well-behaved test. 2 + 2 is always 4, so this always passes.
    assert add(2, 2) == 4


def test_moody_random():
    # A moody test that depends on RANDOMNESS.
    # It picks a random number from 1 to 100 and fails if it's above 90,
    # so it fails roughly 1 time out of 10.
    lucky_number = random.randint(1, 100)
    assert lucky_number <= 90, f"got unlucky number {lucky_number}"


def test_moody_clock():
    # A moody test that depends on the CLOCK.
    # time.time() is the current time in seconds, e.g. 1762160000.4271.
    # The "% 1" keeps only the part after the dot (0.4271).
    # The test fails during the first 3 tenths of every second.
    fraction_of_second = time.time() % 1
    assert fraction_of_second >= 0.3, f"ran too early in the second ({fraction_of_second:.2f})"


def test_add_to_cart():
    # A MESSY test. It puts an apple in the shared cart and never takes it
    # out again. It always passes itself, but it leaves a mess behind.
    shopping_cart.append("apple")
    assert "apple" in shopping_cart


def test_cart_starts_empty():
    # The VICTIM. It expects the cart to be empty. That's true if it runs
    # before test_add_to_cart, and false if it runs after.
    assert len(shopping_cart) == 0, f"cart already has {shopping_cart}"


def test_moody_speed():
    # A moody test that depends on SPEED (a "race").
    # A helper (a "thread") works at the same time as the test itself.
    # The test waits 2 milliseconds and then checks whether the helper has
    # finished. But the helper ALSO takes about 2 milliseconds, so it's a
    # race: sometimes the helper wins, sometimes the test checks too early.
    results = []

    def slow_helper():
        time.sleep(0.002)  # pretend to do some work
        results.append("done")

    helper = threading.Thread(target=slow_helper)
    helper.start()
    time.sleep(0.002)  # BUG: guessing how long to wait. helper.join() would wait properly.
    assert results == ["done"], "checked before the helper finished"
