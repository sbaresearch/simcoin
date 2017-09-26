from unittest import TestCase
from mock import patch
from mock import mock_open
from postprocessing import PostProcessing
from mock import MagicMock
import postprocessing
from textwrap import dedent


class TestPostProcessing(TestCase):
    def setUp(self):
        self.context = MagicMock()
        self.writer = MagicMock()
        self.postprocessing = PostProcessing(self.context, self.writer)

    def test_cut_log(self):
        data = dedent("""
            line1
            line2 start
            line3
            line4 end
            line5
        """).strip()

        m = mock_open(read_data=''.join(data))
        m.return_value.__iter__ = lambda self: self
        m.return_value.__next__ = lambda self: next(iter(self.readline, ''))
        with patch('builtins.open', m) as m_open:
            postprocessing.extract_from_file('source_file', 'destination_file', 'start', 'end')

            self.assertEqual(m_open.call_count, 2)
            self.assertEqual(m_open.call_args_list[0][0][0], 'source_file')
            self.assertEqual(m_open.call_args_list[1][0][0], 'destination_file')

            handle = m_open()
            self.assertEqual(handle.write.call_args_list[0][0][0], 'line2 start\n')
            self.assertEqual(handle.write.call_args_list[1][0][0], 'line3\n')
            self.assertEqual(handle.write.call_args_list[2][0][0], 'line4 end\n')
