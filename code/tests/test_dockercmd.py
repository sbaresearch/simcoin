from unittest import TestCase
import dockercmd
import plan


class TestDockercmd(TestCase):

    def test_run_selfish_node(self):
        cmd = dockercmd.run_selfish_node('127.0.0.1', '127.0.0.2', 'selfish_node_1',
                                         ['192.168.0.1', '192.168.0.2'], 'cmd')
        print(cmd)
        self.assertTrue('--ips-public 192.168.0.1 192.168.0.2' in cmd)
        self.assertTrue(plan.selfish_node_image in cmd)
        self.assertTrue(plan.image in cmd)
        self.assertTrue('  ' not in cmd)
