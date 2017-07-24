from unittest import TestCase
from mock import patch
from mock import mock_open
import nodesconfig
import config


class TestNodesConfig(TestCase):

    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.get_node_type')
    @patch('utils.get_boolean')
    @patch('json.dumps')
    @patch('nodesconfig.check_if_share_sum_is_1')
    def test_create(self, m_check_if_share_sum_is_1, m_dumps, m_get_boolean, m_get_node_type, m_open):
        m_get_node_type.return_value = 'normal'
        nodesconfig.node_types = {'normal': lambda: [{'name': 'node-1'}, {'name': 'node-2'}]}
        m_get_boolean.return_value = False
        m_dumps.return_value = 'mock'
        m_check_if_share_sum_is_1.return_value = True

        nodesconfig.create(False)

        self.assertEqual(m_dumps.call_args[0][0],  [{'name': 'node-1'}, {'name': 'node-2'}])
        m_open.assert_called_with(config.nodes_config_json, 'w')
        handle = m_open()
        self.assertEqual(handle.write.call_args[0][0], 'mock')

    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.get_node_type')
    @patch('utils.get_boolean')
    @patch('json.dumps')
    @patch('nodesconfig.check_if_share_sum_is_1')
    def test_create_two_node_types(self, m_check_if_share_sum_is_1, m_dumps, m_get_boolean, m_get_node_type, m_open):
        m_get_node_type.return_value = 'normal'
        nodesconfig.node_types = {'normal': lambda: [{'name': 'node-1'}]}
        m_get_boolean.side_effect = [True, False]
        m_dumps.return_value = 'mock'
        m_check_if_share_sum_is_1.return_value = True

        nodesconfig.create(False)

        self.assertEqual(m_dumps.call_args[0][0],  [{'name': 'node-1'}, {'name': 'node-1'}])

    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.get_node_type')
    @patch('utils.get_boolean')
    @patch('nodesconfig.check_if_share_sum_is_1')
    @patch('json.dumps')
    def test_create_computation_sum_not_1(self, m_dumps, m_check_if_share_sum_is_1, m_get_boolean, m_get_node_type, m_open):
        m_get_node_type.return_value = 'normal'
        m_check_if_share_sum_is_1.side_effect = [False, True]
        nodesconfig.node_types = {'normal': lambda:  [{'name': 'node-1', 'share': 1}]}
        m_get_boolean.return_value = False
        m_dumps.return_value = 'mock'

        nodesconfig.create(False)

        self.assertEqual(m_check_if_share_sum_is_1.call_count, 2)

    @patch('utils.get_non_negative_int')
    @patch('utils.get_percentage')
    def test_create_normal_node_config(self, m_get_percentage, m_get_non_negative_int):
        m_get_percentage.return_value = 0.1
        m_get_non_negative_int.side_effect = [2, 3, 4]

        nodes = nodesconfig.create_normal_node_config()

        self.assertEqual(nodes, [{'type': 'normal', 'latency': 3, 'share': 0.1},
                                 {'type': 'normal', 'latency': 4, 'share': 0.1}])

    def test_check_if_share_sum_is_1_false(self):
        nodes = [{'share': 0.4}, {'share': 0.4}]

        self.assertFalse(nodesconfig.check_if_share_sum_is_1(nodes))

    def test_check_if_share_sum_is_1_true(self):
        nodes = [{'share': 0.4}, {'share': 0.6}]

        self.assertTrue(nodesconfig.check_if_share_sum_is_1(nodes))
