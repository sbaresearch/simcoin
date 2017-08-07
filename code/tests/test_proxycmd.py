from unittest import TestCase
import proxycmd
from node import ProxyNode
import ipaddress


class TestProxycmd(TestCase):

    def test_run_proxy(self):
        args = 'args1 args2'
        node = ProxyNode('name', ipaddress.ip_address('1.1.1.1'), ipaddress.ip_address('2.2.2.1'), args, 0, None)
        node.outgoing_ips = ['ip1', 'ip2']
        cmd = proxycmd.run_proxy(node, 'hash')
        self.assertTrue('  ' not in cmd)

    def test_get_best_public_block_hash(self):
        cmd = proxycmd.get_best_public_block_hash('node-0')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('get_best_public_block_hash' in cmd)

    def test_start_hash(self):
        cmd = proxycmd.start_hash('node-0')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('start_hash' in cmd)

    def test_exec_cli(self):
        cmd = proxycmd.exec_cli('node-0', 'cmd')

        self.assertTrue('  ' not in cmd)
        self.assertTrue('python cli.py cmd' in cmd)
