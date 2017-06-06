from unittest import TestCase
import dockercmd
import plan
from plan import SelfishNode


class TestDockercmd(TestCase):

    def test_run_selfish_node(self):
        node = SelfishNode('name', 'ip1', 'ip2', 'args')

        cmd = dockercmd.run_selfish_node(node, 'selfish_cmd', 'cmd', 10)

        self.assertTrue(plan.selfish_node_image in cmd)
        self.assertTrue(plan.node_image in cmd)
        self.assertTrue('  ' not in cmd)
