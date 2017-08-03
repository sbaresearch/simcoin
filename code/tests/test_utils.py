from unittest import TestCase
import utils
from mock import patch


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

    @patch('builtins.exit')
    @patch('os.path.isfile')
    def test_check_for_files_file_not_existing(self, m_isfile, m_exit):
        m_isfile.return_value = False

        utils.check_for_file('file.txt')

        self.assertTrue(m_exit.called)

    @patch('builtins.exit')
    @patch('os.path.isfile')
    def test_check_for_files_file_exists(self, m_isfile, m_exit):
        m_isfile.return_value = True

        utils.check_for_file('file.txt')

        self.assertFalse(m_exit.called)
