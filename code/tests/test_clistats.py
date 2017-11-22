from unittest import TestCase
from clistats import CliStats
from mock import MagicMock
from bitcoin.rpc import JSONRPCError


class TestCliStats(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCliStats, self).__init__(*args, **kwargs)

    def setUp(self):
        self.context = MagicMock()
        self.writer = MagicMock()
        self.cli_stats = CliStats(self.context, self.writer)

    def test_calc_consensus_chain_first_node_no_block(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = JSONRPCError({'code': -1, 'message': 'error'})
        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 0)

    def test_calc_consensus_chain_one_node(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash', JSONRPCError({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0], 'hash')

    def test_calc_consensus_chain_multiple_nodes(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCError({'code': -1, 'message': 'error'})]
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCError({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0, '1': node_1}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0], 'hash1')
        self.assertEqual(chain[1], 'hash2')

    def test_calc_consensus_chain_one_node_trailing_back(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', JSONRPCError({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0, '1': node_1}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0], 'hash1')

    def test_calc_consensus_chain_different_chains(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2', 'hash4']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', 'hash3', 'hash4']

        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0, '1': node_1}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0], 'hash1')

    def test_calc_consensus_chain_three_nodes(self):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2', 'hash5']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', 'hash3', 'hash4']
        node_2 = MagicMock()
        node_2.execute_rpc.side_effect = ['hash1', 'hash3', 'hash4']

        self.context.first_block_height = 10
        self.context.nodes = {'0': node_0, '1': node_1, '2': node_2}

        chain = self.cli_stats._calc_consensus_chain()

        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0], 'hash1')

    def test_node_stats(self):
        node_0 = MagicMock()
        node_0.name = 'name'
        node_0.execute_rpc.return_value = [{'status': 'active', 'branchlen': 2}]
        self.context.nodes = {'0': node_0}

        self.cli_stats._persist_node_stats()

        self.assertEqual(self.writer.write_csv.call_args[0][1], ['node', 'status', 'branchlen'])
        self.assertEqual(len(self.writer.write_csv.call_args[0][2]), 1)
