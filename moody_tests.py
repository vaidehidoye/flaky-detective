# moody_tests.py
#
# These are the "suspects" for our detective to investigate.
# A test is just a function. If it finishes normally, it PASSED.
# If an `assert` line is false, Python raises an error and the test FAILED.

import random
import time


def add(a, b):
    """The tiny program we're testing: it adds two numbers."""
    return a + b


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
