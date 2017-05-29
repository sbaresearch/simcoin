from unittest import TestCase
from plan import Plan
from mock import MagicMock
from plan import Node
from plan import SelfishNode


class TestPlan(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPlan, self).__init__(*args, **kwargs)
        self.config = MagicMock()
        self.config.nodes = 100

        self.plan = Plan(self.config)

    def test_set_public_ips_with_two_nodes(self):
        node1 = Node('1', 'ip1')
        node2 = Node('2', 'ip2')
        selfish_node = SelfishNode('3', 'ip3', 'ip_private')
        self.plan.nodes = [node1, node2]
        self.plan.selfish_nodes = [selfish_node]
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].public_ips), 1)

    def test_set_public_ips_with_three_nodes(self):
        node1 = Node('1', 'ip1')
        node2 = Node('2', 'ip2')
        node3 = Node('3', 'ip3')
        selfish_node = SelfishNode('4', 'ip4', 'ip_private')
        self.plan.nodes = [node1, node2, node3]
        self.plan.selfish_nodes = [selfish_node]
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].public_ips), 1)

    def test_set_public_ips_with_four_nodes(self):
        node1 = Node('1', 'ip1')
        node2 = Node('2', 'ip2')
        node3 = Node('3', 'ip3')
        selfish_node1 = SelfishNode('4', 'ip4', 'ip_private')
        selfish_node2 = SelfishNode('5', 'ip5', 'ip_private')
        self.plan.nodes = [node1, node2, node3]
        self.plan.selfish_nodes = [selfish_node1, selfish_node2]
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].public_ips), 2)