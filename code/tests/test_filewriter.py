from unittest import TestCase
from mock import mock_open
from mock import patch
from mock import Mock
import filewriter

class TestFileWriter(TestCase):

    @patch('builtins.open', new_callable=mock_open)
    def test_write_csv(self, m_open):
        elements = Mock()
        elements.vars_to_array.return_value = ['content_1', 'content_2']
        filewriter.write_csv('file.name', ['header_1', 'header_2'], [elements], 'test_tag')

        m_open.assert_called_with('file.name', 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_args_list[0][0][0], 'header_1;header_2;tag\r\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'content_1;content_2;test_tag\r\n')
