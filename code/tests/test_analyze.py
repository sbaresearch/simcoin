from unittest import TestCase
from mock import patch
from mock import mock_open
import config
from parse import RPCExceptionLogLine
from analyze import Analyzer
from mock import Mock


class TestAnalyze(TestCase):

    @patch('builtins.open', new_callable=mock_open)
    def test_create_rpc_exceptions(self, m_open):
        rpc_exceptions = [
            RPCExceptionLogLine('timestamp', 'node-1', 'some_method', 'some_exception')
        ]

        context = Mock()
        context.rpc_exceptions = rpc_exceptions
        context.general_infos = {'tag': 'test'}
        analyzer = Analyzer(context)
        analyzer.create_rpc_exceptions_csv()

        m_open.assert_called_with(config.rpc_exceptions_csv, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_count, 2)
        self.assertEqual(handle.write.call_args_list[0][0][0], 'timestamp;node;method;exception\r\n')
        self.assertEqual(handle.write.call_args_list[1][0][0], 'timestamp;node-1;some_method;some_exception\r\n')
