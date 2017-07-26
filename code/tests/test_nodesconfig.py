from unittest import TestCase
import nodesconfig
from nodesconfig import NodeConfig


class TestNodesConfig(TestCase):

    def test_check_if_share_sum_is_1_false(self):
        nodes = [NodeConfig('type', 'node-0', 0.4, 0), NodeConfig('type', 'node-1', 0.4, 0)]

        self.assertFalse(nodesconfig.check_if_share_sum_is_1(nodes))

    def test_check_if_share_sum_is_1_true(self):
        nodes = [NodeConfig('type', 'node-0', 0.4, 0), NodeConfig('type', 'node-1', 0.6, 0)]

        self.assertTrue(nodesconfig.check_if_share_sum_is_1(nodes))
