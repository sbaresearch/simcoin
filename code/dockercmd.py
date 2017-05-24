import setup


def run_bootstrap_node(cmd):
    return (' '
            ' docker run '
            '   --detach=true '
            '   --net=isolated_network '
            '   --ip=' + setup.ip_bootstrap + ' '
            '   --name=bootstrap'   # container name
            '   ' + setup.image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            '   bash -c "' + cmd + '" '
            ' '
            )


def run_node(name, cmd):
    return (' '
            ' docker run '
            '   --cap-add=NET_ADMIN ' # for `tc`
            '   --detach=true '
            '   --net=isolated_network '
            '   --name=' + name + ' '   # container name
            '   --hostname=' + name + ' '
            '   --volume ' + setup.host_dir(name) + ':' + setup.guest_dir + ' '
            '   ' + setup.image + ' '      # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            '   bash -c "' + cmd + '" '
            ' ')


def rm_node(name):
    return (' '
            ' docker rm --force ' + name + ' & '
            ' ')


def exec_bash(node, command):
    return (' '
            ' docker exec '
            + node +
            ' /bin/sh -c \''
            '    bitcoin-cli -regtest -datadir=' + setup.guest_dir + ' '  # -printtoconsole -daemon
            + command +
            ' \' '
            ' ')


def create_network(ip_range):
        return (' docker network create'
                ' --subnet=' + ip_range +
                ' --driver bridge isolated_network;'
                ' sleep 1 ')


def rm_network():
        return 'docker network rm isolated_network'


def fix_data_dirs_permissions():
        return (' docker run '
                ' --rm --volume ' + setup.root_dir + ':/mnt' + ' ' + setup.image + ' chmod a+rwx --recursive /mnt')
