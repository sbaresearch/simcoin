from unittest import TestCase
import config
from mock import patch
import intervals
from intervals import Node


class TestIntervals(TestCase):

    def test_create_nodes_array(self):
        number_of_nodes = 3
        number_of_selfish_nodes = 2

        nodes = intervals.create_nodes_array(3, 2)

        self.assertEqual(len(nodes), number_of_nodes + number_of_selfish_nodes)

        for i in range(0, number_of_nodes):
            self.assertTrue(config.node_name.format(str(i)) in nodes)
        for i in range(0, number_of_selfish_nodes):
            self.assertTrue(config.selfish_node_name.format(str(i)) in nodes)

    def test_calc_expected_events_two_events_per_interval(self):
        expected_events = intervals.calc_expected_events(10, 0.5)

        self.assertEqual(expected_events, 60)

    def test_calc_expected_events_one_event_every_two_interval(self):
        expected_events = intervals.calc_expected_events(10, 2)

        self.assertEqual(expected_events, 15)

    def test_calc_expected_events_one_event_per_interval(self):
        expected_events = intervals.calc_expected_events(10, 1)

        self.assertEqual(expected_events, 30)

    def test_create_intervals(self):
        end = 4
        tx_per_interval = 2
        node_0 = Node('node-0')
        node_0.block_events = [0.5, 2.1, end]
        node_1 = Node('node-1')
        node_1.block_events = [0.5, 2.1, end]
        nodes = [node_0, node_1]

        event_intervals = intervals.create_intervals(nodes, tx_per_interval, end)

        self.assertEqual(len(event_intervals), 4)
        self.assertEqual(len(event_intervals[0]), 4)
        self.assertEqual(len(event_intervals[1]), 2)
        self.assertEqual(len(event_intervals[2]), 4)
        self.assertEqual(len(event_intervals[3]), 2)
        self.assertTrue('tx ' in event_intervals[0][0])
        self.assertTrue('tx ' in event_intervals[1][0])
        self.assertTrue('tx ' in event_intervals[2][0])
        self.assertTrue('tx ' in event_intervals[3][0])
        self.assertTrue('block ' in event_intervals[0][2])
        self.assertTrue('block ' in event_intervals[0][3])
        self.assertTrue('block ' in event_intervals[2][2])
        self.assertTrue('block ' in event_intervals[2][3])

    def test_create_intervals_with_multiple_blocks_in_one_interval(self):
        end = 4
        node_0 = Node('node-0')
        node_0.block_events = [0.5, 0.6, end]

        with self.assertRaises(Exception) as context:
            intervals.create_intervals([node_0], 0, end)
        self.assertTrue('Intervals per block is too low.' in str(context.exception))

    def test_create_block_events(self):
        block_events = intervals.create_block_events(0.5, 5, 10)

        self.assertEqual(len(block_events), 10)

    @patch('builtins.input', lambda i: '0.25')
    @patch('intervals.calc_expected_events', lambda a, b: 5)
    @patch('intervals.create_nodes_array', lambda a, b: ['node-0', 'node-1', 'node-2', 'selfish-node-0'])
    @patch('intervals.create_block_events', lambda a, b, c: [10, 11, 9])
    def test_create_nodes(self):
        args = Object()
        args.nodes = 2
        args.selfish_nodes = 1
        args.amount_of_intervals = 10
        args.intervals_per_block = 2

        nodes = intervals.create_nodes(args)

        self.assertEqual(len(nodes), 4)
        for node in nodes:
            self.assertEqual(node.block_events, [10, 11, 9])

    @patch('builtins.input', lambda i: '0.6')
    @patch('intervals.calc_expected_events', lambda a, b: 0)
    @patch('intervals.create_nodes_array', lambda a, b: ['node-0', 'node-1'])
    @patch('intervals.create_block_events', lambda a, b, c: [0])
    def test_create_nodes_wrong_sum_of_share(self):
        args = Object()
        args.nodes = 2
        args.selfish_nodes = 1
        args.amount_of_intervals = 10
        args.intervals_per_block = 2

        with self.assertRaises(Exception) as context:
            intervals.create_nodes(args)
        print(context.exception)
        self.assertTrue('Sum of shares should be 1.' in str(context.exception))


class Object(object):
    pass
