from unittest import TestCase
import utils
from mock import patch
from mock import mock_open
from textwrap import dedent
from collections import namedtuple
from argparse import Namespace


class TestUtils(TestCase):

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

    @patch('os.path.isfile', lambda path: True)
    def test_read(self):
        data = dedent("""
            int,float,string
            1,45.5,node-1
        """).strip()

        m = mock_open(read_data=data)
        m.return_value.__iter__ = lambda self: self
        m.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('builtins.open', m):
            data = utils.read_csv('/some.csv')[0]
            self.assertEqual(data.int, 1)
            self.assertEqual(data.float, 45.5)
            self.assertEqual(data.string, 'node-1')

    def test_read_empty_file(self):
        m = mock_open(read_data='')
        m.return_value.__iter__ = lambda self: self
        m.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('builtins.open', m):
            data = utils.read_csv('/some.csv')
            self.assertEqual(data, [])

    @patch('utils.read_csv', lambda file: [])
    @patch('builtins.open', new_callable=mock_open)
    def test_update_args_1(self, m_open):
        utils.update_args(Namespace(int=1, float=1.1, string='test'))

        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertIn('string', handle.write.call_args_list[0][0][0])
        self.assertIn('float', handle.write.call_args_list[0][0][0])
        self.assertIn('int', handle.write.call_args_list[0][0][0])

        self.assertIn('1', handle.write.call_args_list[1][0][0])
        self.assertIn('1.1', handle.write.call_args_list[1][0][0])
        self.assertIn('test', handle.write.call_args_list[1][0][0])

    @patch('utils.read_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_update_args_2(self, m_open, m_read):
        Args = namedtuple('Args', 'int float')
        m_read.return_value = [Args(2, 2.2)]

        utils.update_args(Namespace(int=1, string='test'))

        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)

        self.assertIn('1', handle.write.call_args_list[1][0][0])
        self.assertIn('2.2', handle.write.call_args_list[1][0][0])
        self.assertIn('test', handle.write.call_args_list[1][0][0])
