from unittest import TestCase
import utils


class TestUtils(TestCase):

    def test_check_equal_1(self):
        equal = utils.check_equal([1, 1, 1, 1])

        self.assertTrue(equal)

    def test_check_equal_2(self):
        equal = utils.check_equal([1.0, 1])

        self.assertTrue(equal)

    def test_check_equal_3(self):
        equal = utils.check_equal([1, "1"])

        self.assertFalse(equal)

    def test_check_equal_4(self):
        equal = utils.check_equal(["a", "b", "c"])

        self.assertFalse(equal)

    def test_check_equal_5(self):
        equal = utils.check_equal(["a", "a", "a"])

        self.assertTrue(equal)
