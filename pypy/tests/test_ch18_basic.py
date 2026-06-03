# ch18 section 2 — "Your First Test"
# VERBATIM from the chapter. No code patches required for this snippet to pass.
# Only adaptation: the filename is `test_ch18_basic.py` (not the chapter's
# `test_basic.py`) — pytest default discovery needs the `test_*` prefix
# (see PY-18-04), and we keep the `ch18_` marker for our convention.

from tina4_python.test import Test, assert_equal, assert_true

class BasicTest(Test):

    def test_addition(self):
        assert_equal(2 + 2, 4, "Basic addition should work")

    def test_string_contains(self):
        greeting = "Hello, World!"
        assert_true("World" in greeting, "Greeting should contain 'World'")

    def test_array_length(self):
        items = [1, 2, 3, 4, 5]
        assert_equal(len(items), 5, "List should have 5 items")