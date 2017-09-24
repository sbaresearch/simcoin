from unittest import TestCase
from mock import patch
from mock import mock_open
from clistats import CliStats
from mock import MagicMock
import config
from bitcoinrpc.authproxy import JSONRPCException


class TestCliStats(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCliStats, self).__init__(*args, **kwargs)

    def setUp(self):
        self.context = MagicMock()
        self.writer = MagicMock()
        self.cli_stats = CliStats(self.context, self.writer)

    @patch('clistats.write_consensus_chain')
    def test_persist_consensus_chain_first_node_no_block(self, write_chain):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = JSONRPCException({'code': -1, 'message': 'error'})
        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.persist_consensus_chain()

        self.assertEqual(len(write_chain.call_args[0][1]), 0)

    @patch('clistats.write_consensus_chain')
    def test_persist_consensus_chain_one_node(self, write_chain):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.persist_consensus_chain()

        self.assertEqual(len(write_chain.call_args[0][1]), 1)
        self.assertEqual(write_chain.call_args[0][1][0], 'hash')

    @patch('clistats.write_consensus_chain')
    def test_persist_consensus_chain_multiple_nodes(self, write_chain):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCException({'code': -1, 'message': 'error'})]
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.persist_consensus_chain()

        self.assertEqual(len(write_chain.call_args[0][1]), 2)
        self.assertEqual(write_chain.call_args[0][1][0], 'hash1')
        self.assertEqual(write_chain.call_args[0][1][1], 'hash2')

    @patch('clistats.write_consensus_chain')
    def test_persist_consensus_chain_one_node_trailing_back(self, write_chain):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.persist_consensus_chain()

        self.assertEqual(len(write_chain.call_args[0][1]), 1)
        self.assertEqual(write_chain.call_args[0][1][0], 'hash1')

    def test_node_stats(self):
        node_0 = MagicMock()
        node_0.name = 'name'
        node_0.execute_rpc.return_value = [{'status': 'active', 'branchlen': 2}]
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.persist_node_stats()

        self.assertEqual(self.writer.write_csv.call_args[0][1], ['node', 'status', 'branchlen'])
        self.assertEqual(len(self.writer.write_csv.call_args[0][2]), 1)
