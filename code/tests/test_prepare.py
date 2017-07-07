from unittest import TestCase
import utils
from mock import MagicMock
from mock import patch
from mock import mock_open
import prepare
import config


class TestPrepare(TestCase):

    @patch('prepare.wait_until_height_reached')
    @patch('utils.sleep')
    @patch('prepare.delete_nodes')
    def test_warmup_block_generation(self, __, _, m_wait_until_height_reached):
        node_0 = MagicMock()
        node_1 = MagicMock()
        nodes = [node_0, node_1]

        prepare.give_nodes_spendable_coins(nodes)

        self.assertEqual(m_wait_until_height_reached.call_count, len(nodes) * 2 + 1)
        self.assertEqual(node_0.generate_block.call_count, 2)
        self.assertEqual(node_1.generate_block.call_count, 1)

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('bash.check_output')
    @patch('builtins.open', new_callable=mock_open)
    def test_prepare_simulation_dir(self, m_open, m_check_output, m_makedirs, m_exists):
        m_exists.return_value = False

        prepare.prepare_simulation_dir()

        self.assertEqual(m_makedirs.call_count, 2)
        self.assertEqual(m_check_output.call_count, 2)

        self.assertEqual(m_open.call_count, 2)
        self.assertEqual(m_open.call_args_list[0][0][0], config.blocks_csv)
        self.assertEqual(m_open.call_args_list[1][0][0], config.tx_csv)
        handle = m_open()
        self.assertEqual(handle.write.call_args_list[0][0][0], 'node;block;mine_time;stale_block;size;number_of_tx;'
                                                               'number_of_reached_nodes;propagation_median;propagation_std\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'node;tx;number_of_reached_nodes;propagation_median;propagation_std\n')


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
        node.get_block_count.side_effect = ['0', '9', '10']
        prepare.wait_until_height_reached(node, 10)

        self.assertEqual(m_sleep.call_count, 2)

    @patch('utils.sleep')
    def test_wait_until_height_reached_already_reached(self, m_sleep):
        node = MagicMock()
        node.get_block_count.return_value = '10'
        prepare.wait_until_height_reached(node, 10)

        self.assertFalse(m_sleep.called)
