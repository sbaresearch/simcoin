from unittest import TestCase
import bash
from mock import patch
from mock import mock_open


class TestBash(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestBash, self).__init__(*args, **kwargs)

    @patch('subprocess.check_output')
    def test_check_output(self, mock):
        mock.return_value = b'test\ntest\ttest\t\n\n'

        output = bash.check_output('cmd')

        self.assertEqual(output, 'test\ntest\ttest')

    @patch("builtins.open", mock_open())
    @patch('subprocess.call')
    def test_call_silent(self, mock):
        mock.return_value = b'test'
        output = bash.call_silent('cmd')

        self.assertTrue(str(output), 'test')
