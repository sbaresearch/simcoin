import config
import logging
import bash
import dockercmd
import os
import utils


def warmup_block_generation(nodes):
    logging.info('Begin warmup')

    for i, node in enumerate(nodes):
        wait_until_height_reached(node, i)
        node.generate_block()

    wait_until_height_reached(nodes[0], len(nodes))
    nodes[0].generate_block(config.warmup_blocks)

    for node in nodes:
        wait_until_height_reached(node, config.warmup_blocks + len(nodes))

    logging.info('End of warmup')


def prepare_simulation_dir():
    if not os.path.exists(config.out_dir):
        os.makedirs(config.out_dir)
    if not os.path.exists(config.sim_dir):
        os.makedirs(config.sim_dir)

    bash.check_output('cp {} {}'.format(config.network_config, config.sim_dir))
    bash.check_output('cp {} {}'.format(config.interval_csv, config.sim_dir))

    with open(config.blocks_csv, 'a') as file:
        file.write('node;block\n')


def remove_old_containers_if_exists():
    containers = bash.check_output(dockercmd.ps_containers())
    if len(containers) > 0:
        bash.check_output(dockercmd.remove_all_containers(), lvl=logging.DEBUG)


def recreate_network():
    exit_code = bash.call_silent(dockercmd.inspect_network())
    if exit_code == 0:
        bash.check_output(dockercmd.rm_network())
    bash.check_output(dockercmd.create_network())


def wait_until_height_reached(node, height):
    while int(node.get_block_count()) < height:
        logging.debug('Waiting until height={} is reached...'.format(str(height)))
        utils.sleep(0.2)
