import operator
from cmd import dockercmd

#
# for the 'tc' command 'iproute2' needs to be installed inside the container
# furthermore the container needs to be started with '--cap-add=NET_ADMIN'
#


def create(node, zones, latency):
    sorted_zones = sorted(zones.items(), key=operator.itemgetter(0))

    cmds = [
        'tc qdisc add dev eth0 '
        'root handle 1: prio bands '
        '{}'
        'priomap 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'
        .format(len(zones) + 1)
    ]

    for index, zone_tuple in enumerate(sorted_zones):
        zone = zone_tuple[1]

        cmds.append(
            'tc filter add dev eth0 '
            'parent 1: protocol ip prio {} u32'
            ' match ip dst {} flowid 1:{}'
            .format(index + 1, zone.network, index + 2)
        )

    cmds.append('tc qdisc add dev eth0 parent 1:1 handle 10: netem delay 0ms')

    for index, zone_tuple in enumerate(sorted_zones):
        zone = zone_tuple[1]

        if zone.latency == latency:
            aggregated_latency = latency
        else:
            aggregated_latency = latency + zone.latency

        cmds.append(
            'tc qdisc add dev eth0 '
            'parent 1:{} handle {}: netem delay {}ms'
            .format(index + 2, (index + 2) * 10, aggregated_latency)
        )

    docker_cmds = [dockercmd.exec_cmd(node, cmd) for cmd in cmds]

    return docker_cmds
