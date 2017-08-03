import ipaddress
import config


class Zone:
    def __init__(self):
        self.zones = {}
        self.counter = 0

    def get_ip(self, latency):
        if latency not in self.zones:
            self.counter += 1

            self.zones[latency] = ZoneConfig(ipaddress.ip_network(config.ip_zones.format(self.counter)), latency)
        return next(self.zones[latency].hosts)


class ZoneConfig:
    def __init__(self, network, latency):
        self.network = network
        self.hosts = network.hosts()
        self.latency = latency
