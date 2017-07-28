from unittest import TestCase
import parse
from parse import ParseException
from textwrap import dedent
from mock import patch
from mock import mock_open
from parse import Parser
from mock import Mock
from parse import CreateNewBlock
from parse import UpdateTip
from parse import ReceivedBlock
from parse import BlockStats
import numpy as np
import config


class TestParse(TestCase):

    def setUp(self):

        self.parser = Parser(['node-0', 'node-1', 'node-2'])

    def test_parse_create_new_block(self):
        log_line = '2017-07-27 11:01:22.173139 node-1' \
                   ' CreateNewBlock(): total size: 226 block weight: 904 txs: 1 fees: 0 sigops 400'

        create_new_block = parse.parse_create_new_block(log_line)

        self.assertEqual(create_new_block.timestamp, 1501146082.173139)
        self.assertEqual(create_new_block.node, 'node-1')
        self.assertEqual(create_new_block.total_size, 226)
        self.assertEqual(create_new_block.txs, 1)

    def test_parse_create_new_block_with_other_log_line(self):
        with self.assertRaises(ParseException) as context:
            parse.parse_create_new_block('Some other log_line')

        self.assertTrue("Didn't matched CreateNewBlock log line." in str(context.exception))

    def test_parse_update_tip(self):
        log_line = '2017-07-27 11:01:27.183575 node-1' \
                   ' UpdateTip: new best=1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71' \
                   ' height=106 version=0x20000000 log2_work=7.741467 tx=113' \
                   ' date=\'2017-07-27 11:01:29\' progress=1.000000 cache=0.0MiB(112tx)'

        update_tip = parse.parse_update_tip(log_line)

        self.assertEqual(update_tip.timestamp, 1501146087.183575)
        self.assertEqual(update_tip.node, 'node-1')
        self.assertEqual(update_tip.block_hash, '1d205cac616c0344721d2552482024528883e9fdf7439bfbfc02567060c56d71')
        self.assertEqual(update_tip.height, 106)
        self.assertEqual(update_tip.txs, 113)

    def test_parse_update_tip_with_other_log_line(self):
        with self.assertRaises(ParseException) as context:
            parse.parse_update_tip('Some other log_line')

        self.assertTrue("Didn't matched CreateNewBlock log line." in str(context.exception))

    def test_parse_aggregated_log_first_matching(self):
        data = dedent("""
            line1
            line2
            line3
        """).strip()

        m_parser_1 = Mock()
        m_parser_2 = Mock()

        self.parser.parsers = [m_parser_1, m_parser_2]

        with patch('builtins.open', mock_open(read_data=data)):
            self.parser.parse_aggregated_sim_log()

            self.assertEqual(m_parser_1.call_count, 3)
            self.assertEqual(m_parser_2.call_count, 0)

    def test_parse_aggregated_log_second_matching(self):
        data = dedent("""
            line1
        """).strip()

        m_parser_1 = Mock()
        m_parser_1.side_effect = ParseException()
        m_parser_2 = Mock()

        self.parser.parsers = [m_parser_1, m_parser_2]

        with patch('builtins.open', mock_open(read_data=data)):
            self.parser.parse_aggregated_sim_log()

            self.assertEqual(m_parser_1.call_count, 1)
            self.assertEqual(m_parser_2.call_count, 1)

    @patch('parse.parse_create_new_block', lambda a: CreateNewBlock(None, 'node-0', None, None))
    def test_create_new_block_parser(self):

        self.parser.block_creation_parser('line')

        self.assertTrue(self.parser.nodes_create_blocks['node-0'])

    @patch('parse.parse_update_tip', lambda a: UpdateTip(None, 'node-0', None, None, None))
    def test_update_tip_parser_with_previous_create_new_block(self):
        self.parser.nodes_create_blocks['node-0'] = CreateNewBlock(None, None, None, None)

        self.parser.tip_updated_parser('line')

        self.assertEqual(len(self.parser.blocks), 1)
        self.assertEqual(self.parser.nodes_create_blocks['node-0'], None)

    @patch('parse.parse_update_tip', lambda a: UpdateTip(None, 'node-0', None, None, None))
    def test_update_tip_parser_with_previous_no_create_new_block(self):
        self.parser.tip_updated_parser('line')

        self.assertEqual(len(self.parser.blocks), 0)

    def test_parse_received_block(self):
        log_line = '2017-07-27 15:34:58.122336 node-1 received block' \
                   ' 4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278' \
                   ' peer=0'

        received_block = parse.parse_received_block(log_line)

        self.assertEqual(received_block.timestamp, 1501162498.122336)
        self.assertEqual(received_block.node, 'node-1')
        self.assertEqual(received_block.block_hash, '4ec9b518b23d460c01abaf1c6e32ec46dbbfc8c81c599dd71c0c175e2367f278')

    def test_successfully_reconstructed_block(self):
        log_line = '2017-07-28 08:41:43.637277 node-3 Successfully reconstructed' \
                   ' block 27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c with 1 txn prefilled,' \
                   ' 0 txn from mempool (incl at least 0 from extra pool) and 0 txn requested'

        received_block = parse.parse_successfully_reconstructed_block(log_line)

        self.assertEqual(received_block.timestamp, 1501224103.637277)
        self.assertEqual(received_block.node, 'node-3')
        self.assertEqual(received_block.block_hash, '27ebf5f20b3860fb3a8ed82f0721300bf96c1836252fddd67b60f48d227d3a3c')


    @patch('parse.parse_received_block')
    def test_received_block_parser(self, m_parse_received_block):
        m_parse_received_block.return_value = ReceivedBlock(123, None, 'block_hash')

        self.parser.blocks['block_hash'] = BlockStats(None, None, None, None, None, None)

        self.parser.block_received_parser('line')

        self.assertEqual(self.parser.blocks['block_hash'].receiving_timestamps, np.array([123]))

    @patch('builtins.open', new_callable=mock_open)
    @patch('stats.calc_median_std')
    def test_create_block_csv(self, m_calc_median_std, m_open):
        self.parser.blocks = {
            'block_hash': BlockStats(1, 'node-0', 'block_hash', 2, 3, 4),
        }
        m_calc_median_std.return_value = {'len': 5, 'median': 6, 'std': 7}

        self.parser.blocks['block_hash'].receiving_timestamps = np.array([1, 10])

        self.parser.create_block_csv()

        m_open.assert_called_with(config.blocks_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'block_hash;node;timestamp;height;total_size;'
                                                               'txs;total_received;'
                                                               'median_propagation;std_propagation\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'block_hash;node-0;1;2;3;4;5;6;7\n')

    def test_cut_log(self):
        data = dedent("""
            line1
            line2 {}
            line3
            line4 {}
            line5
        """.format(config.log_line_sim_start, config.log_line_sim_end)).strip()

        with patch('builtins.open', mock_open(read_data=data)) as m_open:
            parse.cut_log()

            self.assertEqual(m_open.call_count, 2)
            self.assertEqual(m_open.call_args_list[0][0][0], config.aggregated_log)
            self.assertEqual(m_open.call_args_list[1][0][0], config.aggregated_sim_log)

            handle = m_open()
            print(handle.write.call_args_list)
            self.assertEqual(handle.write.call_args_list[0][0][0], 'line2 {}\n'.format(config.log_line_sim_start))
            self.assertEqual(handle.write.call_args_list[1][0][0], 'line3\n')
            self.assertEqual(handle.write.call_args_list[2][0][0], 'line4 {}\n'.format(config.log_line_sim_end))
