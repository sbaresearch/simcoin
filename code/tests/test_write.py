from unittest import TestCase
from mock import patch
from mock import mock_open
from mock import Mock
from write import Writer
import config


class TestUtils(TestCase):

    def setUp(self):
        self.writer = Writer('test_tag')

    @patch('fcntl.flock', lambda file, lock: None)
    @patch('builtins.open', new_callable=mock_open)
    def test_write_csv(self, m_open):
        elements = Mock()
        elements.vars_to_array.return_value = ['content_1', 'content_2']
        self.writer.write_csv('file.name', ['header_1', 'header_2'], [elements])

        self.assertEqual(m_open.call_count, 2)
        self.assertEqual(m_open.call_args_list[0][0], (config.postprocessing_dir + 'file.name', 'w'))
        self.assertEqual(m_open.call_args_list[1][0], (config.postprocessing_dir + 'file.name', 'a'))

        handle = m_open()
        self.assertEqual(handle.write.call_args_list[0][0][0], 'header_1,header_2,tag\r\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'content_1,content_2,test_tag\r\n')
