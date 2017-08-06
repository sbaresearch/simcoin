from unittest import TestCase
from node import BitcoinNode
import config
from mock import MagicMock


class TestNode(TestCase):

    def setUp(self):
        self.node = BitcoinNode('node-1', 'ip')

    def test_create_coinbase_transfer_tx(self):
        self.node.execute_rpc = MagicMock(return_value='raw_tx')

        tx = self.node.create_coinbase_transfer_tx()

        self.assertEqual(self.node.available_coins, config.coinbase_amount - 2 * config.smallest_amount)

        self.assertEqual(tx, 'raw_tx')

