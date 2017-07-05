from unittest import TestCase
import ipaddress
import tccmd


class TestTccmd(TestCase):

    def test_add(self):
        cmd = tccmd.add('node', 200)

        self.assertTrue('  ' not in cmd)
        self.assertTrue('200' in cmd)

    def test_add_except_ip(self):
        cmds = tccmd.add_except_ip('node', 200, ipaddress.ip_address('192.168.0.1'))

        self.assertEqual(len(cmds), 5)
        for cmd in cmds:
            self.assertTrue('  ' not in cmd)
