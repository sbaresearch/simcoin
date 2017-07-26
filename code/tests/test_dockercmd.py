from unittest import TestCase
import dockercmd
from node.abstract import Node
import ipaddress
import config


class TestDockercmd(TestCase):

    def test_run_node(self):
        node = Node('name', ipaddress.ip_address('192.168.0.1'))
        cmd = dockercmd.run_node(node, 'cmd')

        self.assertTrue('  ' not in cmd)

    def test_selfish_proxy(self):
        node = Node('name', ipaddress.ip_address('192.168.0.1'))
        cmd = dockercmd.run_selfish_proxy(node, 'cmd')

        self.assertTrue('  ' not in cmd)
        self.assertTrue(config.prefix + node.name in cmd)
