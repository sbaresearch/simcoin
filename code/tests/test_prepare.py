from unittest import TestCase
from mock import MagicMock
from mock import patch
from mock import mock_open
import prepare
from prepare import Prepare
import config
import bitcoin
from bitcoin.wallet import CBitcoinSecret
from mock import Mock


class TestPrepare(TestCase):

    def setUp(self):
        self.context = Mock()
        self.prepare = Prepare(self.context)

        bitcoin.SelectParams('regtest')

    @patch('prepare.wait_until_height_reached')
    @patch('utils.sleep', lambda time: None)
    @patch('prepare.delete_nodes', lambda nodes: None)
    @patch('prepare.get_coinbase_variables', lambda nodes: None)
    @patch('prepare.transfer_coinbase_to_normal_tx', lambda nodes: None)
    @patch('prepare.get_spent_to_address', lambda nodes: None)
    @patch('prepare.calc_number_of_tx_chains', lambda txs_per_tick, block_per_tick, amount_of_nodes: 5)
    def test_warmup_block_generation(self, m_wait_until_height_reached):
        node_0 = MagicMock()
        node_1 = MagicMock()
        nodes = [node_0, node_1]
        self.context.all_bitcoin_nodes.values.return_value = nodes

        self.prepare.give_nodes_spendable_coins()

        self.assertEqual(m_wait_until_height_reached.call_count, len(nodes) * 4 + 1)
        self.assertEqual(node_0.execute_rpc.call_count, 3)
        self.assertEqual(node_1.execute_rpc.call_count, 3)

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('bash.check_output')
    @patch('builtins.open', new_callable=mock_open)
    def test_prepare_simulation_dir(self, m_open, m_check_output, m_makedirs, m_exists):
        m_exists.return_value = False

        prepare.prepare_simulation_dir()

        self.assertEqual(m_makedirs.call_count, 1)
        self.assertEqual(m_check_output.call_count, 4)


    @patch('bash.check_output')
    def test_remove_old_containers_if_exists(self, m_check_output):
        m_check_output.return_value = ['container1', 'container2']

        prepare.remove_old_containers_if_exists()

        self.assertEqual(m_check_output.call_count, 2)

    @patch('bash.check_output')
    def test_remove_old_containers_if_exists_no_old_containers(self, m_check_output):
        m_check_output.return_value = []

        prepare.remove_old_containers_if_exists()

        self.assertEqual(m_check_output.call_count, 1)

    @patch('bash.call_silent')
    @patch('bash.check_output')
    def test_recreate_network(self, m_check_output, m_call_silent):
        m_call_silent.return_value = 0

        prepare.recreate_network()

        self.assertEqual(m_check_output.call_count, 2)
        self.assertEqual(m_call_silent.call_count, 1)

    @patch('bash.call_silent')
    @patch('bash.check_output')
    def test_recreate_network(self, m_check_output, m_call_silent):
        m_call_silent.return_value = -1

        prepare.recreate_network()

        self.assertEqual(m_check_output.call_count, 1)

    @patch('utils.sleep')
    def test_wait_until_height_reached(self, m_sleep):
        node = MagicMock()
        node.execute_rpc.side_effect = ['0', '9', '10']
        prepare.wait_until_height_reached(node, 10)

        self.assertEqual(m_sleep.call_count, 2)

    @patch('utils.sleep')
    def test_wait_until_height_reached_already_reached(self, m_sleep):
        node = MagicMock()
        node.execute_rpc.return_value = '10'
        prepare.wait_until_height_reached(node, 10)

        self.assertFalse(m_sleep.called)

    def test_get_coinbase_variables(self):
        node_1 = MagicMock()
        node_1.tx_chains = []

        node_1.execute_rpc.side_effect = [
            [
                {"txid": 'tx_hash_1', 'address': 'address_hash_1'},
                {"txid": 'tx_hash_2', 'address': 'address_hash_2'}
            ],
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc',
            'cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'
        ]

        prepare.get_coinbase_variables([node_1])

        self.assertEqual(node_1.execute_rpc.call_count, 3)
        self.assertEqual(len(node_1.tx_chains), 2)

        chain_1 = node_1.tx_chains[0]
        self.assertEqual(chain_1.current_unspent_tx, 'tx_hash_1')
        self.assertEqual(chain_1.address, 'address_hash_1')
        self.assertEqual(chain_1.seckey,  CBitcoinSecret('cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'))

        chain_1 = node_1.tx_chains[1]
        self.assertEqual(chain_1.current_unspent_tx, 'tx_hash_2')
        self.assertEqual(chain_1.address, 'address_hash_2')
        self.assertEqual(chain_1.seckey,  CBitcoinSecret('cTCrrgVLfBqEZ1dxmCnEwmiEWzeZHU8uw3CNvLVvbT4CrBeDdTqc'))

    def test_transfer_coinbase_to_normal_tx(self):
        node_1 = MagicMock()

        node_1.create_coinbase_transfer_tx.return_value = 'raw_transaction'
        node_1.execute_rpc.side_effect = [{'hex': 'signed_raw_transaction'}, 'new_tx_hash']

        prepare.transfer_coinbase_to_normal_tx([node_1])

        self.assertEqual(node_1.current_unspent_tx, 'new_tx_hash')
        self.assertEqual(node_1.execute_rpc.call_args_list[0][0][1], 'raw_transaction')
        self.assertEqual(node_1.execute_rpc.call_args_list[1][0][1], 'signed_raw_transaction')

    def test_create_spent_to_address(self):
        node_1 = MagicMock()
        node_1.execute_rpc.return_value = 'spent_to_address'

        prepare.get_spent_to_address([node_1])

        self.assertEqual(node_1.spent_to_address, 'spent_to_address')

    def test_create_spent_to_address_multiple_nodes(self):
        node_1 = MagicMock()
        node_2 = MagicMock()
        nodes = [node_1, node_2]

        prepare.get_spent_to_address(nodes)

        for node in nodes:
            self.assertEqual(node.execute_rpc.call_count, 1)

    def test_calc_number_of_tx_chains(self):
        config.max_in_mempool_ancestors = 25
        amount = prepare.calc_number_of_tx_chains(2, 1/600, 10)

        self.assertEqual(amount, 18)
