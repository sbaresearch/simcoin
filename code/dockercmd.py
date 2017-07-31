import config
import bitcoincmd


def run_node(node, cmd):
    return ('docker run'
            ' --cap-add=NET_ADMIN'  # for `tc`
            ' --detach=true'
            ' --net=' + config.network_name +
            ' --ip=' + str(node.ip) +
            ' --name=' + config.prefix + node.name +  # container name
            ' --hostname=' + config.prefix + node.name +
            ' --volume $PWD/' + config.host_dir(node) + ':' + config.bitcoin_data_dir +
            ' ' + config.node_image +  # image name # src: https://hub.docker.com/r/abrkn/bitcoind/
            ' bash -c "' + cmd + '"')


def run_selfish_proxy(node, cmd):
        return (
                'docker run'
                ' --cap-add=NET_ADMIN'  # for `tc`
                ' --detach=true'
                ' --net=' + config.network_name +
                ' --ip=' + str(node.ip) +
                ' --name=' + config.prefix + node.name +
                ' --hostname=' + config.prefix + node.name +
                ' ' + config.selfish_node_image +
                ' bash -c "' + cmd + '"')


def exec_cmd(node, cmd):
        return 'docker exec {}{} {}'.format(config.prefix, node, cmd)


def create_network():
        return ('docker network create'
                ' --subnet={}  --driver bridge {}'.format(config.ip_range, config.network_name))


def rm_network():
        return 'docker network rm {}'.format(config.network_name)


def fix_data_dirs_permissions():
        return ('docker run '
                ' --rm --volume $PWD/{}:/mnt {}'
                ' chmod a+rwx --recursive /mnt'.format(config.sim_dir, config.node_image))


def rm_container(name):
        return 'docker rm --force {}{}'.format(config.prefix, name)


def ps_containers():
        return 'docker ps -a -q -f "name={}*"'.format(config.prefix)


def remove_all_containers():
        return 'docker rm -f $({})'.format(ps_containers())


def inspect_network():
        return 'docker network inspect {}'.format(config.network_name)
