from unittest import TestCase
from simulationfiles import nodes_config
from simulationfiles.nodes_config import NodeConfig
from mock import patch


class TestNodesConfig(TestCase):

    def test_check_if_share_sum_is_1_false(self):
        nodes = [NodeConfig('group', 'node-0', 0.4, 0, None), NodeConfig('group', 'node-1', 0.4, 0, None)]

        with self.assertRaises(SystemExit) as cm:
            nodes_config.check_if_share_sum_is_1(nodes)

        self.assertEqual(cm.exception.code, -1)

    def test_check_if_share_sum_is_1_true(self):
        nodes = [NodeConfig('group', 'node-0', 0.4, 0, None), NodeConfig('group', 'node-1', 0.6, 0, None)]

        nodes_config.check_if_share_sum_is_1(nodes)

    @patch('bash.call_silent')
    def test_check_if_image_exists(self, m_call_silent):
        node_args = ['a', 'b', 'c', 'd', 'image']
        m_call_silent.return_value = 0

        nodes_config.check_if_image_exists(node_args)

        self.assertTrue(m_call_silent.called)
        self.assertTrue(m_call_silent.call_args[0][0], 'docker inspect image')

    @patch('bash.call_silent')
    def test_check_if_image_exists_image_does_not_exists(self, m_call_silent):
        node_args = ['a', 'b', 'c', 'd', 'image']
        m_call_silent.return_value = -1

        with self.assertRaises(SystemExit) as context:
            nodes_config.check_if_image_exists(node_args)

        self.assertEqual(context.exception.code, -1)
