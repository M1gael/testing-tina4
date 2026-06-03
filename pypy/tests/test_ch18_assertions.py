# ch18 section 3 — Assertion Methods
# VERBATIM PASS examples from the chapter. No code patches required to pass.
# Note: chapter shows 3-arg signatures for assert_true/false/none/not_none
# but every example (and our usage here) uses the 2-arg form. The docs are
# inconsistent with both themselves and the real runtime signature
# (sentinel-default overload — see PY-18-01).
from tina4_python.test import (
    Test,
    assert_equal,
    assert_true,
    assert_false,
    assert_raises,
    assert_not_equal,
    assert_none,
    assert_not_none,
)


class AssertEqualTest(Test):

    def test_equal_numbers(self):
        assert_equal(4, 4, "Should be equal")

    def test_equal_strings(self):
        assert_equal("hello", "hello", "Strings match")


class AssertTrueTest(Test):

    def test_true_literal(self):
        assert_true(True, "Should be true")

    def test_truthy_one(self):
        assert_true(1, "1 is truthy")

    def test_truthy_string(self):
        assert_true("yes", "Non-empty string is truthy")


class AssertFalseTest(Test):

    def test_false_literal(self):
        assert_false(False, "Should be false")

    def test_false_zero(self):
        assert_false(0, "Zero is falsy")

    def test_false_empty_string(self):
        assert_false("", "Empty string is falsy")


class AssertRaisesTest(Test):

    def test_raises_value_error(self):
        assert_raises(
            lambda: int("not-a-number"),
            ValueError,
            "Should raise ValueError"
        )

    def test_raises_zero_division(self):
        assert_raises(
            lambda: 10 / 0,
            ZeroDivisionError,
            "Should raise on division by zero"
        )


class AssertNotEqualTest(Test):

    def test_not_equal_strings(self):
        assert_not_equal("hello", "world", "Strings differ")


class AssertNoneTest(Test):

    def test_none_value(self):
        assert_none(None, "Should be None")


class AssertNotNoneTest(Test):

    def test_not_none_value(self):
        assert_not_none("hello", "Has value")
