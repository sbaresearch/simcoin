from unittest import TestCase
import ipaddress
from simulationfiles.zone import Zone


class TestZone(TestCase):

    def setUp(self):
        self.zone = Zone()

    def test_get_ip(self):

        ip = self.zone.get_ip(100)

        self.assertEqual(ip, ipaddress.IPv4Address('240.1.0.1'))
        self.assertEqual(self.zone.zones[100].latency, 100)
        self.assertEqual(self.zone.zones[100].network, ipaddress.ip_network('240.1.0.0/16'))

    def test_get_ip_second_time_same_latency(self):

        self.zone.get_ip(100)
        ip = self.zone.get_ip(100)

        self.assertEqual(ip, ipaddress.IPv4Address('240.1.0.2'))

    def test_get_ip_second_time_different_latency(self):

        self.zone.get_ip(100)
        ip = self.zone.get_ip(0)

        self.assertEqual(ip, ipaddress.IPv4Address('240.2.0.1'))
