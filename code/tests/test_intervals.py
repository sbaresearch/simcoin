from unittest import TestCase
from mock import patch
import intervals
from node.bitcoinnode import BitcoinNodeConfig


class TestIntervals(TestCase):

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
        node_0 = BitcoinNodeConfig(name='node-0')
        node_1 = BitcoinNodeConfig(name='node-1')
        nodes = [node_0, node_1]
        block_events = {'node-0': [0.5, 2.1, end], 'node-1': [0.5, 2.1, end]}

        event_intervals = intervals.create_intervals(nodes, block_events, tx_per_interval, end)

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
        node_0 = BitcoinNodeConfig('node-0')
        block_events = {'node-0': [0.5, 0.6, end]}

        with self.assertRaises(Exception) as context:
            intervals.create_intervals([node_0], block_events, 0, end)
        self.assertTrue('Intervals per block is too low.' in str(context.exception))

    def test_create_block_series(self):
        block_events = intervals.create_block_series(0.5, 5, 10)

        self.assertEqual(len(block_events), 10)

    @patch('intervals.calc_expected_events', lambda a, b: 5)
    @patch('intervals.create_block_series', lambda a, b, c: [10, 11, 9])
    def test_create_block_events(self):
        nodes = [BitcoinNodeConfig(name='node-0', share=0.5), BitcoinNodeConfig(name='node-1', share=0.5)]
        amount_of_intervals = 10
        intervals_per_block = 2

        block_events = intervals.create_block_events(nodes, amount_of_intervals, intervals_per_block)
        self.assertEqual(len(block_events), 2)
        for block_events in block_events.values():
            self.assertEqual(block_events, [10, 11, 9])
