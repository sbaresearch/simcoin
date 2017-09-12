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
        self.cli_stats = CliStats(self.context)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_first_node_no_block(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = JSONRPCException({'code': -1, 'message': 'error'})
        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.save_consensus_chain()

        mock.assert_called_with(config.consensus_chain_csv, 'w')
        handle = mock()
        handle.write.assert_called_once_with('height;block_hash;tag\r\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_one_node(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'height;block_hash;tag\r\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], '10;hash;test\r\n')

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_multiple_nodes(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCException({'code': -1, 'message': 'error'})]
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', 'hash2', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        lines = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(lines), 3)
        self.assertTrue('10;hash1;test\r\n' in lines)
        self.assertTrue('11;hash2;test\r\n' in lines)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_consensus_chain_one_node_trailing_back(self, mock):
        node_0 = MagicMock()
        node_0.execute_rpc.side_effect = ['hash1', 'hash2']
        node_1 = MagicMock()
        node_1.execute_rpc.side_effect = ['hash1', JSONRPCException({'code': -1, 'message': 'error'})]

        self.context.first_block_height = 10
        self.context.all_bitcoin_nodes = {'0': node_0, '1': node_1}

        self.cli_stats.save_consensus_chain()

        handle = mock()
        lines = [line[0][0] for line in handle.write.call_args_list]
        self.assertEqual(len(lines), 2)
        self.assertTrue('10;hash1;test\r\n' in lines)

    def test_node_stats(self):
        node_0 = MagicMock()
        node_0.name = 'name'
        node_0.execute_rpc.return_value = [{'status': 'active', 'branchlen': 2}]
        self.context.all_bitcoin_nodes = {'0': node_0}
        self.context.tips = []

        self.cli_stats.node_stats()

        self.assertEqual(len(self.context.tips), 1)
