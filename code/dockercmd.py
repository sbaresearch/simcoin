import plan
import bitcoindcmd


def run_bootstrap_node(node, cmd, latency):
    return ('docker run '
            ' --detach=true '
            ' --net=isolated_network '
            ' --ip=' + node.ip + ' '
            ' --name=' + node.name +   # container name
            ' ' + plan.node_image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            '   bash -c "' + slow_network(latency) + cmd + '" ')


def run_node(node, cmd, latency):
    return ('docker run '
            ' --cap-add=NET_ADMIN '  # for `tc`
            ' --detach=true '
            ' --net=isolated_network '
            ' --ip=' + str(node.ip) +
            ' --name=' + node.name + ' '   # container name
            ' --hostname=' + node.name + ' '
            ' --volume ' + plan.host_dir(node.name) + ':' + bitcoindcmd.guest_dir + ' '
            ' ' + plan.node_image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            ' bash -c "' + '; '.join([slow_network(latency), cmd]) + '" ')


def run_selfish_node(node, cmd, latency):
    public_ips = [str(ip) for ip in node.public_ips]
    args = '{} '.format(node.args) if node.args else ''
    selfish_cmd = '; ' .join([slow_network_proxy(latency, node.private_ip),
                              'python main.py ' + args +
                              '--ips-public ' + ' '.join(public_ips)])
    return (
            #
            # public node
            'docker run'
            ' --detach=true'
            ' --net=isolated_network'
            ' --ip=' + str(node.ip) +
            ' --name=' + node.name + '_proxy'
            ' --hostname=' + node.name + '_proxy'
            ' --rm'
            ' ' + plan.selfish_node_image +
            ' bash -c "' + selfish_cmd + '"; '
            #
            # private node
            'docker run'
            ' --detach=true'
            ' --net=isolated_network'
            ' --ip=' + str(node.private_ip) +
            ' --name=' + node.name +
            ' ' + plan.node_image +
            ' bash -c "' + cmd + '"')


def exec_bash(node, command):
        return ('docker exec '
                + node.name +
                ' /bin/sh -c "'
                + command + '"')


def create_network(ip_range):
        return ('docker network create'
                ' --subnet=' + ip_range +
                ' --driver bridge isolated_network')


def rm_network():
        return 'docker network rm isolated_network'


def fix_data_dirs_permissions():
        return ('docker run '
                ' --rm --volume ' + plan.root_dir + ':/mnt' + ' ' + plan.node_image + ' chmod a+rwx --recursive /mnt')


def slow_network(latency):
        # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
        return 'tc qdisc replace dev eth0 root netem delay ' + str(latency) + 'ms'


def slow_network_proxy(latency, private_ip):
        # needed for this cmd: apt install iproute2 and --cap-add=NET_ADMIN
        return ('tc qdisc add dev eth0 root handle 1: prio; '
                'tc filter add dev eth0 parent 1: protocol ip prio 1 u32 '
                'match ip dst ' + str(private_ip) + ' flowid 1:1; '
                'tc filter add dev eth0 parent 1: protocol ip prio 1 u32 '
                'match ip dst ' + plan.ip_range + ' flowid 1:2; '
                'tc qdisc add dev eth0 parent 1:1 handle 10: netem delay 0ms; '
                'tc qdisc add dev eth0 parent 1:2 handle 20: netem delay ' + str(latency) + 'ms')
