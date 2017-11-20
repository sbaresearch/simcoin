from unittest import TestCase
from cmd import dockercmd
from node import Node
import ipaddress
import config


class TestDockercmd(TestCase):

    def test_run_node(self):
        cmd = dockercmd.run_node('node-1', '1.1.1.1', 'image', 'cmd', '/path')

        self.assertTrue('  ' not in cmd)
