import config
import dockercmd

#
# for the 'tc' command 'iproute2' needs to be installed inside the container
# furthermore the container needs to be started with '--cap-add=NET_ADMIN'
#


def add(node, latency):
        return dockercmd.exec_cmd(node, 'tc qdisc add dev eth0 root netem delay {}ms'.format(str(latency)))


def add_except_ip(node, latency, ip):
        cmds = [dockercmd.exec_cmd(node, cmd) for cmd in
                ['tc qdisc add dev eth0 root handle 1: prio',
                 'tc filter add dev eth0 parent 1:0 protocol ip prio 1 u32 match ip dst {} flowid 1:1'.format(str(ip)),
                 'tc filter add dev eth0 parent 1:0 protocol ip prio 2 u32 match ip dst {} flowid 1:2'.format(config.ip_range),
                 'tc qdisc add dev eth0 parent 1:1 handle 10: netem delay 0ms',
                 'tc qdisc add dev eth0 parent 1:2 handle 20: netem delay {}ms'.format(str(latency))]]
        return cmds
