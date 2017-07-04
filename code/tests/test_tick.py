from unittest import TestCase
import config
from mock import patch
import tick


class TestTick(TestCase):

    def test_create_nodes_array(self):
        number_of_nodes = 3
        number_of_selfish_nodes = 2

        nodes = tick.create_nodes_array(3, 2)

        self.assertEqual(len(nodes), number_of_nodes + number_of_selfish_nodes)

        for i in range(0, number_of_nodes):
            self.assertTrue(config.node_name.format(str(i)) in nodes)
        for i in range(0, number_of_selfish_nodes):
            self.assertTrue(config.selfish_node_name.format(str(i)) in nodes)

    def test_calc_expected_events_two_events_per_interval(self):
        expected_events = tick.calc_expected_events(10, 0.5)

        self.assertEqual(expected_events, 60)

    def test_calc_expected_events_one_event_every_two_interval(self):
        expected_events = tick.calc_expected_events(10, 2)

        self.assertEqual(expected_events, 15)

    def test_calc_expected_events_one_event_per_interval(self):
        expected_events = tick.calc_expected_events(10, 1)

        self.assertEqual(expected_events, 30)

    def test_create_events(self):
        events = tick.create_events(0.1, 1, 100)

        self.assertEqual(len(events), 100)

    @patch('tick.check_if_only_block_per_node')
    def test_create_ticks(self, _):
        end = 4
        block_events = [0.5, 2.1, end]
        tx_events = [0.5, 0.9, 1.0, end]
        nodes = ['node-0', 'node-1']

        ticks = tick.create_ticks(block_events, tx_events, end, nodes)

        self.assertEqual(len(ticks), 4)
        self.assertEqual(len(ticks[0]), 3)
        self.assertEqual(len(ticks[1]), 1)
        self.assertTrue('tx ' in ticks[1][0])
        self.assertEqual(len(ticks[2]), 1)
        self.assertTrue('block ' in ticks[2][0])
        self.assertEqual(len(ticks[3]), 0)

    def test_check_if_only_one_block_per_node(self):
        tick.check_if_only_block_per_node(['nodes-1', 'nodes-0'])

    def test_check_if_only_one_block_per_node_with_two_blocks_for_one_node(self):
        with self.assertRaises(Exception) as context:
            tick.check_if_only_block_per_node(['nodes-1', 'nodes-1'])

            self.assertTrue('Block interval is too low. Only one block per node per tick is allowed.' in str(context))
