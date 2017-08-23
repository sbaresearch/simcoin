from unittest import TestCase
import ipaddress
from cmd import tccmd
from simulationfiles.zone import ZoneConfig


class TestTccmd(TestCase):

    def test_create(self):
        zones = {
            0: ZoneConfig(ipaddress.ip_network('240.1.0.0/16'), 0),
            100: ZoneConfig(ipaddress.ip_network('240.2.0.0/16'), 100),
            200: ZoneConfig(ipaddress.ip_network('240.3.0.0/16'), 200),
        }

        cmds = tccmd.create('node-0', zones, 100)

        self.assertTrue('add dev eth0' in cmds[0])
        self.assertTrue('u32 match ip dst 240.1.0.0/16 flowid 1:2' in cmds[1])
        self.assertTrue('u32 match ip dst 240.2.0.0/16 flowid 1:3' in cmds[2])
        self.assertTrue('u32 match ip dst 240.3.0.0/16 flowid 1:4' in cmds[3])
        self.assertTrue('1:1 handle 10: netem delay 0ms' in cmds[4])
        self.assertTrue('1:2 handle 20: netem delay 100ms' in cmds[5])
        self.assertTrue('1:3 handle 30: netem delay 100ms' in cmds[6])
        self.assertTrue('1:4 handle 40: netem delay 300ms' in cmds[7])
