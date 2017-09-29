from unittest import TestCase
from cmd import dockercmd
from node import Node
import ipaddress
import config


class TestDockercmd(TestCase):

    def test_run_node(self):
        node = Node('name', 'group', ipaddress.ip_address('192.168.0.1'), 'image')
        cmd = dockercmd.run_node(node, 'cmd', '/path')

        self.assertTrue('  ' not in cmd)

    def test_selfish_proxy(self):
        node = Node('name', 'group', ipaddress.ip_address('192.168.0.1'), 'image')
        cmd = dockercmd.run_selfish_proxy(node, 'cmd', '/path')

        self.assertTrue('  ' not in cmd)
        self.assertTrue(config.prefix + node.name in cmd)
