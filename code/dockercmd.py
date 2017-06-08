import plan
import bitcoindcmd
import tccmd


def run_bootstrap_node(node, cmd, latency):
    return ('docker run'
            ' --detach=true'
            ' --net=isolated_network'
            ' --ip=' + node.ip +
            ' --name=' + node.name +  # container name
            ' ' + plan.node_image +  # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            ' bash -c "' + '; '.join([tccmd.slow_network(latency), cmd]) + '" ')


def run_node(node, cmd, latency):
    return ('docker run'
            ' --cap-add=NET_ADMIN'  # for `tc`
            ' --detach=true'
            ' --net=isolated_network'
            ' --ip=' + str(node.ip) +
            ' --name=' + node.name +  # container name
            ' --hostname=' + node.name +
            ' --volume ' + plan.host_dir(node) + ':' + bitcoindcmd.guest_dir +
            ' ' + plan.node_image +  # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            ' bash -c "' + '; '.join([tccmd.slow_network(latency), cmd]) + '" ')


def run_selfish_private_node(node, cmd):
    return ('docker run'
            ' --detach=true'
            ' --net=isolated_network'
            ' --ip=' + str(node.ip) +
            ' --name=' + node.name +
            ' --volume ' + plan.host_dir(node) + ':' + bitcoindcmd.guest_dir +
            ' ' + plan.node_image +
            ' bash -c "' + cmd + '"')


def run_selfish_proxy(node, cmd, latency):
        return (
                'docker run'
                ' --cap-add=NET_ADMIN'  # for `tc`
                ' --detach=true'
                ' --net=isolated_network'
                ' --ip=' + str(node.ip) +
                ' --name=' + node.name +
                ' --hostname=' + node.name +
                ' --rm'
                ' ' + plan.selfish_node_image +
                ' bash -c "' + '; '.join([tccmd.slow_network_proxy(latency, node.ip), cmd]) + '"; ')


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
