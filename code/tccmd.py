import config


def slow_network(latency):
        # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
        return 'tc qdisc replace dev eth0 root netem delay ' + str(latency) + 'ms'


def slow_network_proxy(latency, private_ip):
        # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
        return ('tc qdisc add dev eth0 root handle 1: prio; '
                'tc filter add dev eth0 parent 1: protocol ip prio 1 u32 '
                'match ip dst ' + str(private_ip) + ' flowid 1:1; '
                'tc filter add dev eth0 parent 1: protocol ip prio 1 u32 '
                'match ip dst ' + config.ip_range + ' flowid 1:2; '
                'tc qdisc add dev eth0 parent 1:1 handle 10: netem delay 0ms; '
                'tc qdisc add dev eth0 parent 1:2 handle 20: netem delay ' + str(latency) + 'ms')
