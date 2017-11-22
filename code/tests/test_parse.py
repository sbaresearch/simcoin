from unittest import TestCase
import parse
from parse import Parser
from mock import MagicMock
from datetime import datetime
import pytz


class TestParse(TestCase):

    def setUp(self):
        node_0 = MagicMock()
        node_0.name = 'node-0'
        node_1 = MagicMock()
        node_1.name = 'node-1'
        node_2 = MagicMock()
        node_2.name = 'node-2'

        self.context = MagicMock()
        self.writer = MagicMock()
        self.parser = Parser(self.context, self.writer)

    def test_parse_stats_block(self):
        event = parse.BlockCreateEvent.from_log_line(
            '2017-07-27 11:01:22.173139 Simcoin CreateNewBlock():'
            ' hash:45205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71', 'node-1'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 27, 11, 1, 22, 173139, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-1')
        self.assertEqual(event._hash, '45205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71')

    def test_parse_stats_block(self):
        event = parse.BlockStatsEvent.from_log_line(
            '2017-07-27 11:01:22.173139 CreateNewBlock(): total size: 226 block weight:'
            ' 904 txs: 1 fees: 0 sigops 400',
            'node-1'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 27, 11, 1, 22, 173139, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-1')
        self.assertEqual(event._total_size, 226)
        self.assertEqual(event._txs, 1)

    def test_parse_update_tip(self):
        event = parse.UpdateTipEvent.from_log_line(
            '2017-07-27 11:01:27.183575 UpdateTip: '
            'new best=1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71 height=106 version=0x20000000'
            ' log2_work=7.741467 tx=113 date=\'2017-07-27 11:01:29\' progress=1.000000 cache=0.0MiB(112tx)',
            'node-1'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 27, 11, 1, 27, 183575, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-1')
        self.assertEqual(event._hash, '1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71')
        self.assertEqual(event._height, 106)
        self.assertEqual(event._tx, 113)

    def test_parse_received_block(self):
        event = parse.BlockReceivedEvent.from_log_line(
            '2017-07-27 15:34:58.122336 received block'
            ' 4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278'
            ' peer=0',
            'node-1'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 27, 15, 34, 58, 122336, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-1')
        self.assertEqual(event._hash, '4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278')

    def test_successfully_reconstructed_block(self):
        event = parse.BlockReconstructEvent.from_log_line(
            '2017-07-28 08:41:43.637277 Successfully reconstructed'
            ' block 27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c with 1 txn prefilled,'
            ' 0 txn from mempool (incl at least 0 from extra pool) and 0 txn requested',
            'node-3'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 28, 8, 41, 43, 637277, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-3')
        self.assertEqual(event._hash, '27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c')

    def test_parse_add_to_wallet(self):
        event = parse.TxEvent.from_log_line(
            '2017-07-30 07:48:48.337577 AddToWallet'
            ' 2e1b05f9248ae5f29b2234ac0eb86e0fccbacc084ed91937eee7eea248fc9a6a  new',
            'node-1'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 30, 7, 48, 48, 337577, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-1')
        self.assertEqual(event._hash, '2e1b05f9248ae5f29b2234ac0eb86e0fccbacc084ed91937eee7eea248fc9a6a')

    def test_parse_accept_to_memory_pool(self):
        event = parse.TxReceivedEvent.from_log_line(
            '2017-07-30 07:48:42.907223 AcceptToMemoryPool: peer=1:'
            ' accepted 701cd618d630780ac19a78325f24cdd13cbf87279103c7e9cec9fb6382e90ce7'
            ' (poolsz 11 txn, 13 kB)',
            'node-2'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 30, 7, 48, 42, 907223, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-2')
        self.assertEqual(event._hash, '701cd618d630780ac19a78325f24cdd13cbf87279103c7e9cec9fb6382e90ce7')

    def test_parse_peer_logic_validation(self):
        event = parse.PeerLogicValidationEvent.from_log_line(
            '2017-07-31 16:09:28.663985 PeerLogicValidation::NewPoWValidBlock'
            ' sending header-and-ids 107692460326feaa6f0c6c35bb218bdb3ff2adbc0d10a3a36b8252acf54e0c03'
            ' to peer=0',
            'node-0'
        )

        self.assertEqual(event._timestamp, datetime(2017, 7, 31, 16, 9, 28, 663985, pytz.UTC).timestamp())
        self.assertEqual(event._node, 'node-0')
        self.assertEqual(event._hash, '107692460326feaa6f0c6c35bb218bdb3ff2adbc0d10a3a36b8252acf54e0c03')

    def test_parse_tick(self):
        event = parse.TickEvent.from_log_line('2017-08-19 16:05:14.609000 [MainThread  ] [INFO ]  Tick=11 with'
                                              ' planned_start=45.12, actual_start=110.01 and duration=0.9823310375213623,'
                                              ' created txs=101 and blocks=45', 'simcoin'
        )

        self.assertEqual(event._timestamp, datetime(2017, 8, 19, 16, 5, 14, 609000, pytz.UTC).timestamp())
        self.assertEqual(event._source, 'simcoin')
        self.assertEqual(event._number, 11)
        self.assertEqual(event._planned_start, 45.12)
        self.assertEqual(event._actual_start, 110.01)
        self.assertEqual(event._duration, 0.9823310375213623)
        self.assertEqual(event._txs, 101)
        self.assertEqual(event._blocks, 45)

    def test_parse_tx_creation_exception(self):
        event = parse.TxExceptionEvent.from_log_line(
            '2017-08-19 16:05:14.609000 [MainThread  ] [INFO ]  Could not generate tx for node=s-node-1.1.'
            ' Exception="41: too-long-mempool-chain"',
            'simcoin'
        )

        self.assertEqual(event._timestamp, datetime(2017, 8, 19, 16, 5, 14, 609000, pytz.UTC).timestamp())
        self.assertEqual(event._node, 's-node-1.1')
        self.assertEqual(event._source, 'simcoin')
        self.assertEqual(event._exception, '41: too-long-mempool-chain')

    def test_parse_block_creation_exception(self):
        event = parse.BlockExceptionEvent.from_log_line(
            '2017-08-19 16:05:14.609000 [MainThread  ] [INFO ]  Could not generate block for node=s-node-1.2.'
            ' Exception="41: no tx"',
            'simcoin'
        )

        self.assertEqual(event._timestamp, datetime(2017, 8, 19, 16, 5, 14, 609000, pytz.UTC).timestamp())
        self.assertEqual(event._node, 's-node-1.2')
        self.assertEqual(event._source, 'simcoin')
        self.assertEqual(event._exception, '41: no tx')

    def test_parse_rpc_exception(self):
        event = parse.RPCExceptionEvent.from_log_line(
            '2017-08-19 16:05:14.609000 [MainThread  ] [INFO ]  Could not execute RPC-call=getnewaddress'
            ' on node=s-node-1.1 because of error="Connection timeout".'
            ' Reconnecting and retrying, 5 retries left',
            'simcoin'
        )

        self.assertEqual(event._timestamp, datetime(2017, 8, 19, 16, 5, 14, 609000, pytz.UTC).timestamp())
        self.assertEqual(event._node, 's-node-1.1')
        self.assertEqual(event._source, 'simcoin')
        self.assertEqual(event._method, 'getnewaddress')
        self.assertEqual(event._exception, 'Connection timeout')
        self.assertEqual(event._retries_left, 5)
