from unittest import TestCase
from mock import patch
from mock import mock_open
from clistats import CliStats
from utils import Stats
from utils import Values
from mock import MagicMock
import config
import clistats
import numpy as np


class TestCliStats(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCliStats, self).__init__(*args, **kwargs)

    def setUp(self):
        self.context = MagicMock()
        self.cli_stats = CliStats(self.context)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_first_node_no_block(self, mock):
        node_0 = MagicMock()
        node_0.get_block_hash_silent.return_value = -1
        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.save_consensus_chain()

        mock.assert_called_with(config.consensus_chain_csv, 'w')
        handle = mock()
        handle.write.assert_called_once_with('height;block_hash\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_one_node(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = [0, 'hash', -1]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'height;block_hash\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], '10;hash\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_multiple_nodes(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = [0, 'hash1', 0, 'hash2', 1]
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = [0, 'hash1', 0, 'hash2', 1]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        lines = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(lines), 3)
        self.assertTrue('10;hash1\n' in lines)
        self.assertTrue('11;hash2\n' in lines)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_one_node_trailing_back(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = [0, 'hash1', 0, 'hash2']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = [0, 'hash1', 1]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        lines = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(lines), 2)
        self.assertTrue('10;hash1\n' in lines)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_chains(self, mock):
        self.cli_stats.save_chains()

        mock.assert_called_with(config.chains_csv, 'w')
        handle = mock()
        handle.write.assert_called_once_with('node;block_hashes\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_chains_with_nodes(self, mock):
        node_0 = MagicMock()
        node_0.name = 'node-0'
        node_0.execute_rpc.side_effect = [6, 'hash1', 'hash2']
        node_1 = MagicMock()
        node_1.name = 'node-1'
        node_1.execute_rpc.side_effect = [7, 'hash11', 'hash22', 'hash33']
        self.context.first_block_height = 5
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.save_chains()

        handle = mock()
        lines = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(lines), 3)
        self.assertTrue('node-1;hash11;hash22;hash33\n' in lines)
        self.assertTrue('node-0;hash1;hash2\n' in lines)

    @patch('builtins.open', new_callable=mock_open)
    @patch('clistats.tips_statistics')
    def test_node_stats(self, m_tips_statistics, m_open):
        node_0 = MagicMock()
        node_0.name = 'name'
        self.context.all_bitcoin_nodes = {'0': node_0}

        tips_stats = {
            'headers-only': Values.from_array([1, 3]),
            'total': Values.from_array([1, 5]),
            'valid-fork': Values.from_array([1, 7]),
            'valid-headers': Values.from_array([1, 9]),
        }
        for _, tip_stats in tips_stats.items():
            tip_stats.calc()

        m_tips_statistics.return_value = tips_stats

        self.cli_stats.node_stats()

        m_open.assert_called_with(config.nodes_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 7)
        self.assertEqual(handle.write.call_args_list[0][0][0],
                         'name;'
                         'headers_only;headers_only_median_branchlen;headers_only_std_branchlen;'
                         'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                         'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;'
                         'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;\n')

        self.assertEqual(handle.write.call_args_list[1][0][0], 'name')
        self.assertEqual(handle.write.call_args_list[2][0][0], ';2;2.0;1.0')
        self.assertEqual(handle.write.call_args_list[3][0][0], ';2;3.0;2.0')
        self.assertEqual(handle.write.call_args_list[4][0][0], ';2;4.0;3.0')
        self.assertEqual(handle.write.call_args_list[5][0][0], ';2;5.0;4.0')
        self.assertEqual(handle.write.call_args_list[6][0][0], '\n')

    def test_tips_statistics_unknown_status(self):
        tips = [{'status': 'unknown'}]
        with self.assertRaises(SystemExit) as context:
            clistats.tips_statistics(tips)

        self.assertEqual(context.exception.code, -1)

    def test_tips_statistics_both(self):
        tips = [{'status': 'active'}, {'status': 'valid-headers', 'branchlen': 2},
                {'status': 'valid-fork', 'branchlen': 3}, {'status': 'headers-only', 'branchlen': 4}]
        stats = clistats.tips_statistics(tips)

        self.assertEqual(stats['valid-headers'].stats.median, [2])
        self.assertEqual(stats['valid-fork'].stats.median, [3])
        self.assertEqual(stats['headers-only'].stats.median, [4])
        self.assertTrue(item in [2, 3, 4] for item in stats)

    def test_calc_median_std_no_values(self):
        array = np.array([])
        statistics = Stats.from_array(array)

        self.assertTrue(np.isnan(statistics.median))
        self.assertTrue(np.isnan(statistics.std))
        self.assertEqual(statistics.count, 0)

    def test_calc_median_std(self):
        array = np.array([1, 2])
        statistics = Stats.from_array(array)

        self.assertEqual(statistics.median, 1.5)
        self.assertEqual(statistics.std, 0.5)
        self.assertEqual(statistics.count, 2)
