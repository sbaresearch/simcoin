from unittest import TestCase
from simulationfiles import nodes_config
from simulationfiles.nodes_config import NodeConfig


class TestNodesConfig(TestCase):

    def test_check_if_share_sum_is_1_false(self):
        nodes = [NodeConfig('type', 'node-0', 0.4, 0, None), NodeConfig('type', 'node-1', 0.4, 0, None)]

        self.assertFalse(nodes_config.check_if_share_sum_is_1(nodes))

    def test_check_if_share_sum_is_1_true(self):
        nodes = [NodeConfig('type', 'node-0', 0.4, 0, None), NodeConfig('type', 'node-1', 0.6, 0, None)]
        nodes = [NodeConfig('type', 'node-0', 0.4, 0, None), NodeConfig('type', 'node-1', 0.6, 0, None)]

        self.assertTrue(nodes_config.check_if_share_sum_is_1(nodes))
