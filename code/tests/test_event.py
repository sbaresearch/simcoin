from unittest import TestCase
from event import Event
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import mock_open
from bitcoin.rpc import JSONRPCError
import event


class TestEvent(TestCase):

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    def test_execute_multiple_cmds(self, m_sleep, m_time):
        m_file = mock_open(read_data=''.join(
            'cmd1,cmd2,cmd3'
        ))
        m_file.return_value.__iter__ = lambda self: self
        m_file.return_value.__next__ = lambda self: next(iter(self.readline, ''))

        with patch('builtins.open', m_file):
            mock = MagicMock()
            mock.args.tick_duration = 1
            e = Event(mock)
            e._execute_cmd = MagicMock()

            m_time.return_value = 0

            e.execute()

            self.assertEqual(e._execute_cmd.call_count, 3)
            self.assertTrue(m_sleep.called)

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    def test_execute_multiple_lines(self, m_sleep, m_time):
        m_file = mock_open(read_data=''.join(
            'cmd1\n'
            'cmd2'
        ))
        m_file.return_value.__iter__ = lambda self: self
        m_file.return_value.__next__ = lambda self: next(iter(self.readline, ''))

        with patch('builtins.open', m_file):
            mock = MagicMock()
            mock.args.tick_duration = 1
            e = Event(mock)
            e._execute_cmd = MagicMock()

            m_time.return_value = 0

            e.execute()

            self.assertEqual(e._execute_cmd.call_count, 2)
            self.assertTrue(m_sleep.call_count, 2)

    @patch('utils.check_for_file', lambda file: None)
    @patch('logging.error')
    def test_execute_with_exce_execute_cmd(self, m_error):
        m_file = mock_open(read_data=''.join(
            'cmd1'
        ))
        m_file.return_value.__iter__ = lambda self: self
        m_file.return_value.__next__ = lambda self: next(iter(self.readline, ''))

        with patch('builtins.open', m_file):
            mock = MagicMock()
            mock.args.tick_duration = 0
            e = Event(mock)
            e._execute_cmd = MagicMock()
            e._execute_cmd.side_effect = Exception('mock')

            e.execute()
            self.assertRegex(m_error.call_args[0][0], 'Simulation could not .*')

    def test_execute_cmd_with_block_cmd(self):
        node_1 = MagicMock()
        cmd = 'block node-1'
        e = Event(MagicMock())
        e._context.nodes = {'node-1': node_1}
        e._execute_cmd(cmd)

        self.assertTrue(node_1.generate_blocks.called)

    def test_execute_cmd_with_block_cmd_with_empty_cmd(self):
        node_1 = MagicMock()

        e = Event(MagicMock())
        e.generate_tx = MagicMock()
        e._execute_cmd('')

        self.assertFalse(node_1.execute_rpc.called)
        self.assertFalse(e.generate_tx.called)

    def test_execute_cmd_with_tx_tmd(self):
        node = MagicMock()
        cmd = 'tx node-1'

        e = Event(MagicMock())
        e.generate_tx = MagicMock()
        e._context.nodes = {'node-1': node}
        e._execute_cmd(cmd)

        self.assertTrue(node.generate_tx.called)

    def test_execute_cmd_with_unknown_cmd(self):
        cmd = 'unknown node-1'
        e = Event(MagicMock())
        e._context.nodes = {'node-1': {}}

        with self.assertRaises(Exception) as context:
            e._execute_cmd(cmd)

        self.assertTrue('Unknown cmd' in str(context.exception))

    def test_execute_cmd_with_exception(self):
        context = MagicMock()
        node = MagicMock()
        node.generate_tx.side_effect = JSONRPCError({'code': -1, 'message': 'test_message'})
        context.nodes = {'node-1': node}

        e = Event(context)
        e._execute_cmd('tx node-1')

    def test_calc_analyze_skip_ticks_1(self):
        tick_count = event._calc_analyze_skip_ticks(.1, 50)
        self.assertEqual(tick_count, 10)

    def test_calc_analyze_skip_ticks_2(self):
        tick_count = event._calc_analyze_skip_ticks(.1, .05)
        self.assertEqual(tick_count, 20)

    def test_calc_analyze_skip_ticks_3(self):
        tick_count = event._calc_analyze_skip_ticks(100, 50)
        self.assertEqual(tick_count, 1)
