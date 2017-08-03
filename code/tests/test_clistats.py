from unittest import TestCase
from mock import patch
from mock import mock_open
from clistats import CliStats
from clistats import Stats
from mock import MagicMock
import config
import clistats
import numpy as np


class TestCliStats(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCliStats, self).__init__(*args, **kwargs)

    def setUp(self):
        self.executor = MagicMock()
        self.cli_stats = CliStats(self.executor)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_first_node_no_block(self, mock):
        node_0 = MagicMock()
        node_0.get_block_hash_silent.return_value = -1
        self.executor.first_block_height = 10
        self.executor.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.save_consensus_chain()

        mock.assert_called_with(config.consensus_chain_csv, 'w')
        handle = mock()
        handle.write.assert_called_once_with('height;block_hash\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_one_node(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = [0, 'hash', -1]

        self.executor.first_block_height = 10
        self.executor.all_bitcoin_nodes = {'0': node_0}

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

        self.executor.first_block_height = 10
        self.executor.all_bitcoin_nodes = {'0': node_0, '1': node_1}

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

        self.executor.first_block_height = 10
        self.executor.all_bitcoin_nodes = {'0': node_0, '1': node_1}

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
        self.executor.first_block_height = 5
        self.executor.all_bitcoin_nodes = {'0': node_0, '1': node_1}

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
        self.executor.all_bitcoin_nodes = {'0': node_0}
        m_tips_statistics.return_value = \
            {
                'total': Stats(1, 2, 3),
                'valid-headers': Stats(11,  22, 33),
                'valid-fork': Stats(111, 222, 333),
                'headers-only': Stats(1111, 2222, 3333,)
            }

        self.cli_stats.node_stats()

        m_open.assert_called_with(config.nodes_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0],
                         'name;'
                         'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                         'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;'
                         'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;'
                         'headers_only;headers_only_median_branchlen;headers_only_std_branchlen;\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'name;1;2;3;11;22;33;111;222;333;1111;2222;3333\n')

    def test_tips_statistics_unknown_status(self):
        tips = [{'status': 'unknown'}]
        with self.assertRaises(Exception) as context:
            clistats.tips_statistics(tips)

        self.assertTrue('Unknown tip type=unknown' in str(context.exception))

    def test_tips_statistics_both(self):
        tips = [{'status': 'active'}, {'status': 'valid-headers', 'branchlen': 2},
                {'status': 'valid-fork', 'branchlen': 3}, {'status': 'headers-only', 'branchlen': 4}]
        stats = clistats.tips_statistics(tips)

        self.assertEqual(stats['valid-headers'].median, [2])
        self.assertEqual(stats['valid-fork'].median, [3])
        self.assertEqual(stats['headers-only'].median, [4])
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
