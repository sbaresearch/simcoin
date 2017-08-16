from unittest import TestCase
from mock import patch
from mock import mock_open
from parse import BlockStats
import numpy as np
import config
from parse import TxStats
from parse import CheckingMempoolLogLine
from analyze import Analyzer
from event import TransactionException
from mock import Mock


class TestAnalyze(TestCase):

    @patch('builtins.open', new_callable=mock_open)
    def test_create_block_csv(self, m_open):
        block_stats = BlockStats(1, 'node-0', 'block_hash', 3, 4)
        block_stats.height = 2
        blocks = {
            'block_hash': block_stats,
        }

        blocks['block_hash'].receiving_timestamps = np.array([5, 7])

        context = Mock()
        context.parsed_blocks = blocks
        context.consensus_chain = ['block_hash']
        analyzer = Analyzer(context)
        analyzer.create_block_csv()

        m_open.assert_called_with(config.blocks_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'block_hash;node;timestamp;stale;height;total_size;'
                                                               'txs;total_received;'
                                                               'median_propagation;std_propagation\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'block_hash;node-0;1;False;2;3;4;2;6.0;1.0\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_create_block_csv_stale_block(self, m_open):
        block_stats = BlockStats(1, 'node-0', 'block_hash', 3, 4)
        block_stats.height = 2
        blocks = {
            'block_hash': block_stats,
        }

        blocks['block_hash'].receiving_timestamps = np.array([5, 7])

        context = Mock()
        context.parsed_blocks = blocks
        context.consensus_chain = []
        analyzer = Analyzer(context)
        analyzer.create_block_csv()

        m_open.assert_called_with(config.blocks_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_args_list[1][0][0], 'block_hash;node-0;1;True;2;3;4;2;6.0;1.0\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_create_tx_csv(self, m_open):
        txs = {
            'tx_hash': TxStats(1, 'node-0', 'tx_hash'),
        }

        txs['tx_hash'].receiving_timestamps = np.array([5, 7])

        context = Mock()
        context.parsed_txs = txs
        analyzer = Analyzer(context)
        analyzer.create_tx_csv()

        m_open.assert_called_with(config.txs_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'tx_hash;node;timestamp;'
                                                               'total_accepted;median_propagation;std_propagation\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'tx_hash;node-0;1;2;6.0;1.0\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_create_tx_exceptions_csv(self, m_open):
        tx_exceptions = [
            TransactionException('node-1', 'timestamp', 'error_message')
        ]

        context = Mock()
        context.tx_exceptions = tx_exceptions
        analyzer = Analyzer(context)
        analyzer.create_tx_exceptions_csv()

        m_open.assert_called_with(config.tx_exceptions_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'node;timestamp;error_message\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'node-1;timestamp;error_message\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_create_mempool_snapshots_csv(self, m_open):
        mempool_snapshots = [
            CheckingMempoolLogLine('timestamp', 'node-1', 45, 36)
        ]

        context = Mock()
        context.mempool_snapshots = mempool_snapshots
        analyzer = Analyzer(context)
        analyzer.create_mempool_snapshots_csv()

        m_open.assert_called_with(config.mempool_snapshots_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'timestamp;node;txs;inputs\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'timestamp;node-1;45;36\n')
