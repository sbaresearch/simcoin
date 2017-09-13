from unittest import TestCase
from mock import patch
from mock import mock_open
from postprocessing import PostProcessing
from mock import MagicMock
import config
import postprocessing
from textwrap import dedent
from collections import OrderedDict


class TestPostProcessing(TestCase):
    def setUp(self):
        self.context = MagicMock()
        self.postprocessing = PostProcessing(self.context)

    @patch('builtins.open', new_callable=mock_open)
    @patch('bash.check_output_without_log', lambda cmd: '3\n4\n')
    @patch('postprocessing.prefix_log', lambda lines, node: lines)
    @patch('postprocessing.add_line_number', lambda lines: lines)
    def test_aggregate_logs(self, m_open):
        node_0 = MagicMock()
        node_0.cat_log_cmd.return_value = "1\n2\n"
        self.context.all_nodes = {'node-0': node_0}
        self.context.path.aggregated_log = '/path'

        self.postprocessing.aggregate_logs()

        self.assertEqual(m_open.call_args[0][0], '/path')
        handle = m_open()
        self.assertEqual(handle.write.call_args_list[0][0][0], '1\n2\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], '3\n4\n')

    @patch('builtins.open', new_callable=mock_open)
    @patch('bash.check_output_without_log', lambda cmd: '')
    @patch('postprocessing.prefix_log', lambda lines, node: lines)
    @patch('postprocessing.add_line_number', lambda lines: lines)
    def test_aggregate_logs_two_nodes(self, m_open):
        node_0 = MagicMock()
        node_1 = MagicMock()
        node_0.cat_log_cmd.return_value = "1\n2\n"
        node_1.cat_log_cmd.return_value = "11\n22\n"
        self.context.all_nodes = OrderedDict(sorted({'node-0': node_0, 'node-1': node_1}.items(), key=lambda t: t[0]))

        self.postprocessing.aggregate_logs()

        handle = m_open()
        self.assertEqual(handle.write.call_args_list[0][0][0], '1\n2\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], '11\n22\n')

    def test_prefix_log_no_changes(self):
        lines = ['2017-07-05 14:33:35.324000 test', '2017-07-05 14:33:35.324000 test']
        received = postprocessing.prefix_log(lines, 'node-0')

        expected = ['2017-07-05 14:33:35.324000 node-0 test', '2017-07-05 14:33:35.324000 node-0 test']
        self.assertEqual(received, expected)

    def test_prefix_log(self):
        lines = ['2017-07-05 14:33:35.324000 test', 'test']
        received = postprocessing.prefix_log(lines, 'node-0')

        expected = ['2017-07-05 14:33:35.324000 node-0 test', '2017-07-05 14:33:35.324000 node-0 test']
        self.assertEqual(received, expected)

    def test_cut_log(self):
        data = dedent("""
            line1
            line2 {}
            line3
            line4 {}
            line5
        """.format(config.log_line_sim_start, config.log_line_sim_end)).strip()
        self.context.path.aggregated_log = '/path_log'
        self.context.path.aggregated_sim_log = '/path_sim_log'

        with patch('builtins.open', mock_open(read_data=data)) as m_open:
            self.postprocessing.cut_log()

            self.assertEqual(m_open.call_count, 2)
            self.assertEqual(m_open.call_args_list[0][0][0], '/path_log')
            self.assertEqual(m_open.call_args_list[1][0][0], '/path_sim_log')

            handle = m_open()
            self.assertEqual(handle.write.call_args_list[0][0][0], 'line2 {}\n'.format(config.log_line_sim_start))
            self.assertEqual(handle.write.call_args_list[1][0][0], 'line3\n')
            self.assertEqual(handle.write.call_args_list[2][0][0], 'line4 {}\n'.format(config.log_line_sim_end))
