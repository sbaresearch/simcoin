import ipaddress
import config
from collections import namedtuple


class Zone:
    def __init__(self):
        self.zones = {}
        self.counter = 0

    def get_ip(self, latency):
        if latency not in self.zones:
            self.counter += 1

            network = ipaddress.ip_network(config.ip_zones.format(self.counter))
            self.zones[latency] = ZoneConfig(network, network.hosts(), latency)
        return next(self.zones[latency].hosts)


ZoneConfig = namedtuple('ZoneConfig', 'network hosts latency')
