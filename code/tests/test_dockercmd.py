from unittest import TestCase
import dockercmd
import plan
from plan import SelfishNode


class TestDockercmd(TestCase):

    def test_run_selfish_node(self):
        node = SelfishNode('name', 'ip1', 'ip2')
        node.public_ips = ['192.168.0.1', '192.168.0.2']

        cmd = dockercmd.run_selfish_node(node, 'cmd')

        self.assertTrue('--ips-public 192.168.0.1 192.168.0.2' in cmd)
        self.assertTrue(plan.selfish_node_image in cmd)
        self.assertTrue(plan.image in cmd)
        self.assertTrue('  ' not in cmd)
