from unittest import TestCase
import checkargs
import argparse


class TestCheckargs(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCheckargs, self).__init__(*args, **kwargs)

    def test_check_positive(self):
        value = checkargs.check_positive(0)

        self.assertEqual(value, 0)

    def test_check_positive_exception(self):
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            checkargs.check_positive(-1)

        self.assertTrue('-1 is an invalid positive value' in str(context.exception))

    def test_check_percentage_zero(self):
        value = checkargs.check_percentage(0)
        self.assertEqual(value, 0)

    def test_check_percentage_one(self):
        value = checkargs.check_percentage(1)
        self.assertEqual(value, 1)

    def test_check_percentage_negative(self):
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            checkargs.check_percentage(-0.1)

        self.assertTrue('-0.1 is an invalid percentage value [0,1]' in str(context.exception))

    def test_check_percentage_over_one(self):
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            checkargs.check_percentage(1.1)

        self.assertTrue('1.1 is an invalid percentage value [0,1]' in str(context.exception))

    def test_check_percentage_with_string(self):
        with self.assertRaises(ValueError):
            checkargs.check_percentage('test')

    def test_check_positive_float(self):
        value = checkargs.check_positive(1.1)

        self.assertEqual(value, 1.1)

    def test_check_positive_float_with_string(self):
        with self.assertRaises(ValueError):
            checkargs.check_positive_float('test')

    def test_check_positive_int_with_float(self):
        with self.assertRaises(argparse.ArgumentTypeError) as context:
            checkargs.check_positive_int(1.1)
        self.assertTrue('1.1 is an invalid integer' in str(context.exception))

    def test_check_positive_int(self):
        checkargs.check_positive_int('10')
