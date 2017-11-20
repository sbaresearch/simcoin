from unittest import TestCase
from node import BitcoinNode
from mock import patch
from bitcoin.wallet import CBitcoinSecret
import bitcoin

bitcoin.SelectParams('regtest')


class TestNode(TestCase):

    def setUp(self):
        self.node = BitcoinNode('node-1', 'group', 'ip', 'image', '/path')

    @patch('node.BitcoinNode.execute_rpc')
    def test_get_coinbase_variables(self, m_execute_rpc):
        m_execute_rpc.side_effect = [
            [
                {"txid": 'tx_hash_1', 'address': 'address_hash_1', 'amount': 50},
                {"txid": 'tx_hash_2', 'address': 'address_hash_2', 'amount': 25}
            ],
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc',
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'
        ]

        self.node.create_tx_chains()

        self.assertEqual(m_execute_rpc.call_count, 3)
        self.assertEqual(len(self.node._tx_chains), 2)

        chain_1 = self.node._tx_chains[0]
        self.assertEqual(chain_1.current_unspent_tx, 'tx_hash_1')
        self.assertEqual(chain_1.address, 'address_hash_1')
        self.assertEqual(chain_1.seckey,  CBitcoinSecret('cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'))
        self.assertEqual(chain_1.amount, 5000000000)

        chain_2 = self.node._tx_chains[1]
        self.assertEqual(chain_2.current_unspent_tx, 'tx_hash_2')
        self.assertEqual(chain_2.address, 'address_hash_2')
        self.assertEqual(chain_2.amount, 2500000000)
