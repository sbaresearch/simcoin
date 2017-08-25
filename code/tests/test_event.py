from unittest import TestCase
from event import Event
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import mock_open
from bitcoinrpc.authproxy import JSONRPCException
from textwrap import dedent


class TestEvent(TestCase):

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    def test_execute_multiple_cmds(self, m_sleep, m_time):
        data = dedent("""
            cmd1;cmd2;cmd3
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            mock = Mock()
            mock.args.tick_duration = 1
            e = Event(mock)
            e.execute_cmd = Mock()

            m_time.return_value = 0

            e.execute()

            self.assertEqual(e.execute_cmd.call_count, 3)
            self.assertTrue(m_sleep.called)

    @patch('time.time')
    @patch('utils.sleep')
    @patch('utils.check_for_file', lambda file: None)
    def test_execute_multiple_lines(self, m_sleep, m_time):
        data = dedent("""
            cmd1
            cmd2
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            mock = Mock()
            mock.args.tick_duration = 1
            e = Event(mock)
            e.execute_cmd = Mock()

            m_time.return_value = 0

            e.execute()

            self.assertEqual(e.execute_cmd.call_count, 2)
            self.assertTrue(m_sleep.call_count, 2)

    @patch('time.time')
    @patch('utils.check_for_file', lambda file: None)
    def test_execute(self, m_time):
        data = dedent("""
            cmd1;cmd2;cmd3
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            mock = Mock()
            mock.args.tick_duration = 0
            e = Event(mock)
            e.execute_cmd = Mock()

            m_time.side_effect = [0, 1, 10]

            with self.assertRaises(SystemExit) as context:
                e.execute()
            self.assertEqual(context.exception.code, -1)

    @patch('utils.check_for_file', lambda file: None)
    def test_execute_with_exce_execute_cmd(self):
        data = dedent("""
            cmd1
        """).strip()

        with patch('builtins.open', mock_open(read_data=data)):
            mock = Mock()
            mock.args.tick_duration = 0
            e = Event(mock)
            e.execute_cmd = Mock()
            e.execute_cmd.side_effect = Exception('mock')

            with self.assertRaises(Exception) as context:
                e.execute()
            self.assertTrue('mock' in str(context.exception))

    def test_execute_cmd_with_block_cmd(self):
        node_1 = Mock()
        cmd = 'block node-1'
        e = Event(Mock())
        e.context.all_bitcoin_nodes = {'node-1': node_1}
        e.execute_cmd(cmd)

        self.assertTrue(node_1.execute_rpc.called)

    def test_execute_cmd_with_block_cmd_with_empty_cmd(self):
        node_1 = Mock()

        e = Event(Mock())
        e.generate_tx = Mock()
        e.execute_cmd('')

        self.assertFalse(node_1.execute_rpc.called)
        self.assertFalse(e.generate_tx.called)

    def test_execute_cmd_with_tx_tmd(self):
        node = Mock()
        cmd = 'tx node-1'

        e = Event(Mock())
        e.generate_tx = Mock()
        e.context.all_bitcoin_nodes = {'node-1': node}
        e.execute_cmd(cmd)

        self.assertTrue(node.generate_tx.called)

    def test_execute_cmd_with_unknown_cmd(self):
        cmd = 'unknown node-1'
        e = Event(Mock())
        e.context.all_bitcoin_nodes = {'node-1': {}}

        with self.assertRaises(Exception) as context:
            e.execute_cmd(cmd)

        self.assertTrue('Unknown cmd' in str(context.exception))

    def test_execute_cmd_with_exception(self):
        context = Mock()
        node = Mock()
        node.generate_tx.side_effect = JSONRPCException({'code': -1, 'message': 'test_message'})
        context.all_bitcoin_nodes = {'node-1': node}

        e = Event(context)
        e.execute_cmd('tx node-1')
