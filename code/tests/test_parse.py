from unittest import TestCase
import parse
from parse import ParseException
from textwrap import dedent
from mock import patch
from mock import mock_open
from parse import Parser
from mock import Mock
from parse import TickLogLine
from parse import CreateNewBlockLogLine
from parse import UpdateTipLogLine
from parse import CheckingMempoolLogLine
from parse import LogLineWithHash
from parse import BlockStats
import numpy as np
from datetime import datetime
from parse import TxStats


class TestParse(TestCase):

    def setUp(self):
        node_0 = Mock()
        node_0.name = 'node-0'
        node_1 = Mock()
        node_1.name = 'node-1'
        node_2 = Mock()
        node_2.name = 'node-2'

        self.context = Mock()
        self.context.parsed_blocks = {}
        self.context.parsed_txs = {}
        self.context.mempool_snapshots = []
        self.context.tick_infos = []
        self.context.all_bitcoin_nodes.values.return_value = [node_0, node_1, node_2]
        self.parser = Parser(self.context)

    def test_parse_create_new_block(self):
        create_new_block = parse.parse_create_new_block(
            '2017-07-27 11:01:22.173139 node-1 CreateNewBlock(): total size: 226 block weight:'
            ' 904 txs: 1 fees: 0 sigops 400'
        )

        self.assertEqual(create_new_block.timestamp, datetime(2017, 7, 27, 11, 1, 22, 173139).timestamp())
        self.assertEqual(create_new_block.node, 'node-1')
        self.assertEqual(create_new_block.total_size, 226)
        self.assertEqual(create_new_block.txs, 1)

    def test_parse_create_new_block_with_other_log_line(self):
        with self.assertRaises(ParseException) as context:
            parse.parse_create_new_block('Some other log_line')

        self.assertTrue("Didn't matched CreateNewBlock log line." in str(context.exception))

    def test_parse_update_tip(self):
        update_tip = parse.parse_update_tip(
            '2017-07-27 11:01:27.183575 node-1 UpdateTip: '
            'new best=1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71 height=106 version=0x20000000'
            ' log2_work=7.741467 tx=113 date=\'2017-07-27 11:01:29\' progress=1.000000 cache=0.0MiB(112tx)')

        self.assertEqual(update_tip.timestamp, datetime(2017, 7, 27, 11, 1, 27, 183575).timestamp())
        self.assertEqual(update_tip.node, 'node-1')
        self.assertEqual(update_tip.block_hash, '1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71')
        self.assertEqual(update_tip.height, 106)
        self.assertEqual(update_tip.tx, 113)

    def test_parse_update_tip_with_other_log_line(self):
        with self.assertRaises(ParseException) as context:
            parse.parse_update_tip('Some other log_line')

        self.assertTrue("Didn't matched CreateNewBlock log line." in str(context.exception))

    def test_parse_aggregated_log_first_matching(self):
        data = dedent("""
            line1
            line2
            line3
        """).strip()

        self.parser.parsers = ['parser_1', 'parser_2']
        m_execute_parser_function = Mock()
        self.parser.execute_parser_function = m_execute_parser_function

        with patch('builtins.open', mock_open(read_data=data)):
            self.parser.execute()

            self.assertEqual(m_execute_parser_function.call_count, 3)

    def test_parse_aggregated_log_second_matching(self):
        data = dedent("""
            line1
        """).strip()

        self.parser.parsers = ['parser_1', 'parser_2']
        m_execute_parser_function = Mock()
        m_execute_parser_function.side_effect = [ParseException(), None]
        self.parser.execute_parser_function = m_execute_parser_function

        with patch('builtins.open', mock_open(read_data=data)):
            self.parser.execute()

            self.assertEqual(m_execute_parser_function.call_count, 2)

    @patch('parse.parse_create_new_block', lambda a: CreateNewBlockLogLine(None, 'node-0', None, None))
    def test_create_new_block_parser(self):

        self.parser.block_creation_parser('line')

        self.assertTrue(self.parser.nodes_create_blocks['node-0'])

    @patch('parse.parse_update_tip', lambda a: UpdateTipLogLine(None, 'node-0', 'block_hash', 45, None))
    def test_update_tip_parser_with_previous_create_new_block(self):
        self.parser.nodes_create_blocks['node-0'] = CreateNewBlockLogLine(None, None, None, None)

        self.parser.tip_updated_parser('line')

        self.assertEqual(len(self.context.parsed_blocks), 1)
        parsed_block = self.context.parsed_blocks['block_hash']
        self.assertEqual(parsed_block.height, 45)
        self.assertEqual(self.parser.nodes_create_blocks['node-0'], None)

    @patch('parse.parse_update_tip', lambda a: UpdateTipLogLine(None, 'node-0', 'block_hash', 45, None))
    def test_update_tip_parser_with_block_stats_already_set(self):
        self.context.parsed_blocks['block_hash'] = BlockStats(None, None, None, None, None)

        self.parser.tip_updated_parser('line')

        self.assertEqual(len(self.context.parsed_blocks), 1)
        self.assertEqual(self.context.parsed_blocks['block_hash'].height, 45)
        self.assertEqual(self.parser.nodes_create_blocks['node-0'], None)

    @patch('parse.parse_update_tip', lambda a: UpdateTipLogLine(None, 'node-0', None, None, None))
    def test_update_tip_parser_with_previous_no_create_new_block(self):
        self.parser.tip_updated_parser('line')

        self.assertEqual(len(self.context.parsed_blocks), 0)

    def test_parse_received_block(self):
        log_line_with_hash = parse.parse_received_block(
            '2017-07-27 15:34:58.122336 node-1 received block'
            ' 4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278'
            ' peer=0'
        )

        self.assertEqual(log_line_with_hash.timestamp, datetime(2017, 7, 27, 15, 34, 58, 122336).timestamp())
        self.assertEqual(log_line_with_hash.node, 'node-1')
        self.assertEqual(log_line_with_hash.obj_hash, '4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278')

    def test_successfully_reconstructed_block(self):
        log_line_with_hash = parse.parse_successfully_reconstructed_block(
            '2017-07-28 08:41:43.637277 node-3 Successfully reconstructed'
            ' block 27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c with 1 txn prefilled,'
            ' 0 txn from mempool (incl at least 0 from extra pool) and 0 txn requested'
        )

        self.assertEqual(log_line_with_hash.timestamp, datetime(2017, 7, 28, 8, 41, 43, 637277).timestamp())
        self.assertEqual(log_line_with_hash.node, 'node-3')
        self.assertEqual(log_line_with_hash.obj_hash, '27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c')

    @patch('parse.parse_received_block')
    def test_received_block_parser(self, m_parse_received_block):
        m_parse_received_block.return_value = LogLineWithHash(10, None, 'block_hash')

        self.context.parsed_blocks['block_hash'] = BlockStats(1, None, None, None, None)

        self.parser.block_received_parser('line')

        self.assertEqual(self.context.parsed_blocks['block_hash'].receiving_timestamps, np.array([9]))

    @patch('parse.parse_successfully_reconstructed_block')
    def test_block_reconstructed_parser(self, m_parse_successfully_reconstructed_block):
        m_parse_successfully_reconstructed_block.return_value = LogLineWithHash(10, None, 'block_hash')

        self.context.parsed_blocks['block_hash'] = BlockStats(1, None, None, None, None)

        self.parser.block_reconstructed_parser('line')

        self.assertEqual(self.context.parsed_blocks['block_hash'].receiving_timestamps, np.array([9]))

    @patch('parse.parse_accept_to_memory_pool')
    def test_tx_received_parser(self, m_parse_accept_to_memory_pool):
        m_parse_accept_to_memory_pool.return_value = LogLineWithHash(10, None, 'tx_hash')

        self.context.parsed_txs['tx_hash'] = TxStats(1, None, None)

        self.parser.tx_received_parser('line')

        self.assertEqual(self.context.parsed_txs['tx_hash'].receiving_timestamps, np.array([9]))

    def test_parse_add_to_wallet(self):
        log_line_with_hash = parse.parse_add_to_wallet(
            '2017-07-30 07:48:48.337577 node-1 AddToWallet'
            ' 2e1b05f9248ae5f29b2234ac0eb86e0fccbacc084ed91937eee7eea248fc9a6a  new'
        )

        self.assertEqual(log_line_with_hash.timestamp, datetime(2017, 7, 30, 7, 48, 48, 337577).timestamp())
        self.assertEqual(log_line_with_hash.node, 'node-1')
        self.assertEqual(log_line_with_hash.obj_hash, '2e1b05f9248ae5f29b2234ac0eb86e0fccbacc084ed91937eee7eea248fc9a6a')

    def test_parse_accept_to_memory_pool(self):
        log_line_with_hash = parse.parse_accept_to_memory_pool(
            '2017-07-30 07:48:42.907223 node-2 AcceptToMemoryPool: peer=1:'
            ' accepted 701cd618d630780ac19a78325f24cdd13cbf87279103c7e9cec9fb6382e90ce7'
            ' (poolsz 11 txn, 13 kB)'
        )

        self.assertEqual(log_line_with_hash.timestamp, datetime(2017, 7, 30, 7, 48, 42, 907223).timestamp())
        self.assertEqual(log_line_with_hash.node, 'node-2')
        self.assertEqual(log_line_with_hash.obj_hash, '701cd618d630780ac19a78325f24cdd13cbf87279103c7e9cec9fb6382e90ce7')

    @patch('parse.parse_accept_to_memory_pool', lambda line: LogLineWithHash(
        2, 'node-0', 'tx_hash'
    ))
    def test_received_parser(self):
        self.context.parsed_txs['tx_hash'] = TxStats(0, 'node-1', 'tx_hash')

        self.parser.tx_received_parser('line')

        self.assertEqual(self.context.parsed_txs['tx_hash'].receiving_timestamps, np.array([2]))

    @patch('parse.parse_add_to_wallet', lambda line: LogLineWithHash(
        2, 'node-0', 'tx_hash'
    ))
    def test_received_parser(self):
        self.parser.tx_creation_parser('line')

        self.assertTrue(self.context.parsed_txs['tx_hash'])

        self.assertTrue(self.context.parsed_txs['tx_hash'].tx_hash, 'tx_hash')

    def test_parse_peer_logic_validation(self):
        log_line_with_hash = parse.parse_peer_logic_validation(
            '2017-07-31 16:09:28.663985 node-0 PeerLogicValidation::NewPoWValidBlock'
            ' sending header-and-ids 107692460326feaa6f0c6c35bb218bdb3ff2adbc0d10a3a36b8252acf54e0c03'
            ' to peer=0'
        )

        self.assertEqual(log_line_with_hash.timestamp, datetime(2017, 7, 31, 16, 9, 28, 663985).timestamp())
        self.assertEqual(log_line_with_hash.node, 'node-0')
        self.assertEqual(log_line_with_hash.obj_hash, '107692460326feaa6f0c6c35bb218bdb3ff2adbc0d10a3a36b8252acf54e0c03')

    @patch('parse.parse_peer_logic_validation', lambda a: LogLineWithHash(None, 'node-0', 'block_hash'))
    def test_peer_logic_validation_parse(self):
        self.parser.nodes_create_blocks['node-0'] = CreateNewBlockLogLine(None, None, None, None)

        self.parser.peer_logic_validation_parser('line')

        self.assertEqual(len(self.context.parsed_blocks), 1)
        self.assertEqual(self.parser.nodes_create_blocks['node-0'], None)

    @patch('parse.parse_peer_logic_validation', lambda a: UpdateTipLogLine(None, 'node-0', None, None, None))
    def test_update_tip_parser_with_previous_no_create_new_block(self):
        self.parser.peer_logic_validation_parser('line')

        self.assertEqual(len(self.context.parsed_blocks), 0)

    def test_parse_checking_mempool(self):
        checking_mempool = parse.parse_checking_mempool(
            '2017-07-31 16:09:28.663985 node-0 Checking mempool with 5878 transactions and 5999 inputs'
        )

        self.assertEqual(checking_mempool.timestamp, datetime(2017, 7, 31, 16, 9, 28, 663985).timestamp())
        self.assertEqual(checking_mempool.node, 'node-0')
        self.assertEqual(checking_mempool.txs, 5878)
        self.assertEqual(checking_mempool.inputs, 5999)

    @patch('parse.parse_checking_mempool', lambda a: CheckingMempoolLogLine(None, None, None, None))
    def test_checking_mempool_parser(self):
        self.parser.checking_mempool_parser('line')

        self.assertEqual(len(self.context.mempool_snapshots), 1)

    def test_parse_tick(self):
        tick_log_line = parse.parse_tick_log_line(
            '2017-08-19 16:05:14.609000 simcoin [MainThread  ] [INFO ]  Sleep 0.9823310375213623 seconds for next tick.'
        )

        self.assertEqual(tick_log_line.timestamp, datetime(2017, 8, 19, 16, 5, 14, 609000).timestamp())
        self.assertEqual(tick_log_line.sleep_time, 0.9823310375213623)

    @patch('parse.parse_tick_log_line', lambda a: TickLogLine(None, None))
    def test_checking_mempool_parser(self):
        self.parser.tick_parser('line')

        self.assertEqual(len(self.context.tick_infos), 1)