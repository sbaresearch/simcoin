import ipaddress


class Zone:
    def __init__(self):
        self.zones = {}
        self.counter = 0

    def get_ip(self, latency):
        if latency in self.zones:
            return next(self.zones[latency])
        else:
            self.counter += 1

            hosts = ipaddress.ip_network('240.{}.0.0/16'.format(self.counter)).hosts()
            self.zones[latency] = hosts
            return next(hosts)
