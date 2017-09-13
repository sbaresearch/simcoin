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

    @patch('prepare.wait_until_height_reached', lambda node, height: None)
    @patch('utils.sleep', lambda time: None)
    @patch('prepare.calc_number_of_tx_chains', lambda txs_per_tick, block_per_tick, amount_of_nodes: 5)
    def test_warmup_block_generation(self):
        node_0 = MagicMock()
        node_1 = MagicMock()
        nodes = [node_0, node_1]
        self.context.all_bitcoin_nodes.values.return_value = nodes

        self.prepare.give_nodes_spendable_coins()

        self.assertEqual(node_0.execute_rpc.call_count, 3)
        self.assertEqual(node_1.execute_rpc.call_count, 3)

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('bash.check_output')
    @patch('builtins.open', new_callable=mock_open)
    def test_prepare_simulation_dir(self, m_open, m_check_output, m_makedirs, m_exists):
        m_exists.return_value = False

        self.prepare.prepare_simulation_dir()

        self.assertEqual(m_makedirs.call_count, 2)
        self.assertEqual(m_check_output.call_count, 5)


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

    def test_calc_number_of_tx_chains(self):
        config.max_in_mempool_ancestors = 25
        amount = prepare.calc_number_of_tx_chains(2, 1/600, 10)

        self.assertEqual(amount, 18)
