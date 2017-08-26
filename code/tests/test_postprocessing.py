from unittest import TestCase
from mock import patch
from mock import mock_open
from postprocessing import PostProcessing
from mock import MagicMock
import config
import postprocessing
from textwrap import dedent


class TestPostProcessing(TestCase):
    def setUp(self):
        self.context = MagicMock()
        self.postprocessing = PostProcessing(self.context)

    @patch('builtins.open', new_callable=mock_open)
    @patch('bash.check_output_without_log')
    @patch('postprocessing.prefix_log')
    def test_aggregate_logs(self, m_prefix, m_bash, m_open):
        node_0 = MagicMock()
        self.context.all_nodes = {'node-0': node_0}
        m_prefix.return_value = ['1', '2']

        self.postprocessing.aggregate_logs()

        self.assertEqual(m_open.call_args[0][0], config.aggregated_log)
        handle = m_open()
        self.assertEqual(handle.write.call_args[0][0], '1\n2\n')

        self.assertEqual(m_bash.call_count, 2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('bash.check_output_without_log')
    @patch('postprocessing.prefix_log')
    def test_aggregate_logs_two_nodes(self, m_prefix, m_bash, m_open):
        node_0 = MagicMock()
        node_1 = MagicMock()
        m_prefix.side_effect = [['1', '2'], ['11', '22']]
        self.context.all_nodes = {'node-0': node_0, 'node-1': node_1}

        self.postprocessing.aggregate_logs()

        handle = m_open()
        contents = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(contents), 2)
        self.assertTrue('1\n2\n' in contents)
        self.assertTrue('11\n22\n' in contents)

        self.assertEqual(m_bash.call_count, 2)

    def test_prefix_log_no_changes(self):
        lines = ['2017-07-05 14:33:35.324000 test', '2017-07-05 14:33:35.324000 test']
        received = postprocessing.prefix_log(lines, 'node-0')

        expected = ['2017-07-05 14:33:35.324000 node-0 1 test', '2017-07-05 14:33:35.324000 node-0 2 test']
        self.assertEqual(received, expected)

    def test_prefix_log(self):
        lines = ['2017-07-05 14:33:35.324000 test', 'test']
        received = postprocessing.prefix_log(lines, 'node-0')

        expected = ['2017-07-05 14:33:35.324000 node-0 1 test', '2017-07-05 14:33:35.324000 node-0 2 test']
        self.assertEqual(received, expected)

    def test_cut_log(self):
        data = dedent("""
            line1
            line2 {}
            line3
            line4 {}
            line5
        """.format(config.log_line_sim_start, config.log_line_sim_end)).strip()

        with patch('builtins.open', mock_open(read_data=data)) as m_open:
            postprocessing.cut_log()

            self.assertEqual(m_open.call_count, 2)
            self.assertEqual(m_open.call_args_list[0][0][0], config.aggregated_log)
            self.assertEqual(m_open.call_args_list[1][0][0], config.aggregated_sim_log)

            handle = m_open()
            self.assertEqual(handle.write.call_args_list[0][0][0], 'line2 {}\n'.format(config.log_line_sim_start))
            self.assertEqual(handle.write.call_args_list[1][0][0], 'line3\n')
            self.assertEqual(handle.write.call_args_list[2][0][0], 'line4 {}\n'.format(config.log_line_sim_end))
