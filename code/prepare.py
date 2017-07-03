import config
import logging
import bash
import dockercmd
import os
import utils


class Prepare:
    def __init__(self, _executor):
        self.executor = _executor

    def warmup_block_generation(self):
        logging.info('Begin warmup')

        for i, node in enumerate(self.executor.all_bitcoind_nodes.values()):
            wait_until_height_reached(node, i)
            bash.check_output(node.generate_block())

        node = self.executor.all_bitcoind_nodes[config.reference_node]
        wait_until_height_reached(node, len(self.executor.all_bitcoind_nodes))
        bash.check_output(node.generate_block(config.warmup_blocks))
        [wait_until_height_reached(node, config.warmup_blocks + len(self.executor.all_bitcoind_nodes))
         for node in self.executor.all_bitcoind_nodes.values()]

        logging.info('End of warmup')


def create_simulation_dir():
    if not os.path.exists(config.out_dir):
        os.makedirs(config.out_dir)
    if not os.path.exists(config.sim_dir):
        os.makedirs(config.sim_dir)


def remove_old_containers_if_exists():
    containers = bash.check_output(dockercmd.ps_containers())
    if len(containers) > 0:
        bash.check_output(dockercmd.remove_all_containers(), lvl=logging.DEBUG)


def recreate_network():
    exit_code = bash.call_silent(dockercmd.inspect_network())
    if exit_code == 0:
        bash.check_output(dockercmd.rm_network())
    bash.check_output(dockercmd.create_network(config.ip_range))


def wait_until_height_reached(node, height):
    while int(bash.check_output(node.get_block_count())) < height:
        logging.debug('Waiting until height={} is reached...'.format(str(height)))
        utils.sleep(0.2)
