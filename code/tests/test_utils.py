from unittest import TestCase
import utils
from mock import patch
from mock import mock_open
import argparse
from textwrap import dedent


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

    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dumps')
    def test_update_args_json_update_args(self, m_dump, m_load, m_open, m_is_file):
        m_is_file.return_value = True
        args = argparse.Namespace()
        args.test = 1

        m_load.return_value = {'test': 0}

        utils.update_args_json(args)

        self.assertEqual(m_dump.call_args[0][0], {'test': 1})

    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dumps')
    def test_update_args_json_add_args(self, m_dump, m_load, m_open, m_is_file):
        m_is_file.return_value = True
        args = argparse.Namespace()
        args.unknown_arg = 1

        m_load.return_value = {'test': 0}

        utils.update_args_json(args)

        self.assertEqual(m_dump.call_args[0][0], {'test': 0, 'unknown_arg': 1})

    def test_read(self):
        data = dedent("""
            int,float,string
            1,45.5,node-1
        """).strip()

        m = mock_open(read_data=data)
        m.return_value.__iter__ = lambda self: self
        m.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('builtins.open', m):
            data = utils.read_args()
            self.assertEqual(data.int, 1)
            self.assertEqual(data.float, 45.5)
            self.assertEqual(data.string, 'node-1')

    def test_read_empty_file(self):
        m = mock_open(read_data='')
        m.return_value.__iter__ = lambda self: self
        m.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('builtins.open', m):
            data = utils.read_args()
            self.assertEqual(data, None)
