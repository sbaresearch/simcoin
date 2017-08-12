from unittest import TestCase
from node import BitcoinNode
import config
from mock import MagicMock
from bitcoin.wallet import CBitcoinSecret
import bitcoin

bitcoin.SelectParams('regtest')


class TestNode(TestCase):

    def setUp(self):
        self.node = BitcoinNode('node-1', 'ip', 'image')

    def test_get_coinbase_variables(self):
        self.node.execute_rpc = MagicMock()
        self.node.execute_rpc.side_effect = [
            [
                {"txid": 'tx_hash_1', 'address': 'address_hash_1'},
                {"txid": 'tx_hash_2', 'address': 'address_hash_2'}
            ],
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc',
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'
        ]

        self.node.create_tx_chains()

        self.assertEqual(self.node.execute_rpc.call_count, 3)
        self.assertEqual(len(self.node.tx_chains), 2)

        chain_1 = self.node.tx_chains[0]
        self.assertEqual(chain_1.current_unspent_tx, 'tx_hash_1')
        self.assertEqual(chain_1.address, 'address_hash_1')
        self.assertEqual(chain_1.seckey,  CBitcoinSecret('cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'))

        chain_1 = self.node.tx_chains[1]
        self.assertEqual(chain_1.current_unspent_tx, 'tx_hash_2')
        self.assertEqual(chain_1.address, 'address_hash_2')
        self.assertEqual(chain_1.seckey,  CBitcoinSecret('cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'))
