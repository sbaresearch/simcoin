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
        self.config.nodes = 2
        self.config.selfish_nodes = 1
        self.plan = Plan(self.config)
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].proxy.public_ips), 1)

    def test_set_public_ips_with_three_nodes(self):
        self.config.nodes = 3
        self.config.selfish_nodes = 1
        self.plan = Plan(self.config)
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].proxy.public_ips), 1)

    def test_set_public_ips_with_four_nodes(self):
        self.config.nodes = 3
        self.config.selfish_nodes = 2
        self.plan = Plan(self.config)
        self.config.connectivity = 0.5

        self.plan.set_public_ips()

        self.assertTrue(len(self.plan.selfish_nodes[0].proxy.public_ips), 2)
