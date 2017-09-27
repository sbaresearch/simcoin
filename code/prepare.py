import config
import logging
import bash
from cmd import dockercmd
import os
import utils
import math
from multiprocessing.dummy import Pool as ThreadPool
import itertools
from bitcoinrpc.authproxy import HTTP_TIMEOUT


class Prepare:
    def __init__(self, context):
        self.context = context
        self.pool = ThreadPool(5)

    def execute(self):
        logging.info('Begin of prepare step')

        self.prepare_simulation_dir()
        remove_old_containers_if_exists()
        recreate_network()

        utils.sleep(1)

        self.give_nodes_spendable_coins()

        self.start_nodes()

        self.pool.close()

        logging.info('End of prepare step')

    def give_nodes_spendable_coins(self):
        nodes = list(self.context.all_bitcoin_nodes.values())

        self.pool.map(start_node, nodes)

        amount_of_tx_chains = calc_number_of_tx_chains(
            self.context.args.txs_per_tick,
            self.context.args.blocks_per_tick,
            len(nodes)
        )
        logging.info('Each node receives {} tx-chains'.format(amount_of_tx_chains))


        for i, node in enumerate(nodes):
            for node_to_be_connected in nodes[max(0, i - 5):i]:
                node.execute_rpc('addnode', str(node_to_be_connected.ip),
                                 'add')

        utils.sleep(3)

        for i, node in enumerate(nodes):
            wait_until_height_reached(node, i * amount_of_tx_chains)
            node.execute_cli('generate', amount_of_tx_chains)
            logging.info('Generated {} blocks for node={} for their tx-chains'.format(amount_of_tx_chains, node.name))

        wait_until_height_reached(nodes[0], amount_of_tx_chains * len(nodes))
        nodes[0].execute_cli('generate',
                           config.blocks_needed_to_make_coinbase_spendable)
        current_height = config.blocks_needed_to_make_coinbase_spendable + amount_of_tx_chains * len(nodes)

        self.pool.starmap(wait_until_height_reached, zip(nodes, itertools.repeat(current_height)))

        self.pool.map(transfer_coinbase_tx_to_normal_tx, nodes)

        for i, node in enumerate(nodes):
            wait_until_height_reached(node, current_height + i)
            node.execute_rpc('generate', 1)

        current_height += len(nodes)
        self.context.first_block_height = current_height

        self.pool.starmap(wait_until_height_reached, zip(nodes, itertools.repeat(current_height)))

        for i, node in enumerate(nodes):
            node.rm()
            logging.info('node.rm {}'.format(node.name))

        # self.pool.map(rm_node, nodes)

    def start_nodes(self):
        nodes = self.context.all_bitcoin_nodes.values()

        self.pool.starmap(start_node, zip(
            nodes,
            itertools.repeat(config.rpc_simulation_timeout),
            itertools.repeat(self.context.first_block_height)
        ))

        start_hash = self.context.one_normal_node.execute_rpc('getbestblockhash')
        self.pool.starmap(start_proxy_node, zip(
            self.context.selfish_node_proxies.values(),
            itertools.repeat(start_hash),
            itertools.repeat(self.context.one_normal_node)
        ))

        self.pool.map(connect, self.context.nodes.values())

        self.pool.starmap(add_latency, zip(
            self.context.all_public_nodes.values(),
            itertools.repeat(self.context.zone.zones)
        ))

        logging.info('All nodes for the simulation are started')
        utils.sleep(3 + len(self.context.all_nodes) * 0.2)

    def prepare_simulation_dir(self):
        if not os.path.exists(self.context.run_dir):
            os.makedirs(self.context.run_dir)

        if os.path.islink(config.soft_link_to_run_dir):
            bash.check_output('unlink {}'.format(config.soft_link_to_run_dir))
        bash.check_output('ln -s {} {}'.format(self.context.run_dir, config.soft_link_to_run_dir))
        os.makedirs(config.postprocessing_dir)

        bash.check_output('cp {} {}'.format(config.network_csv, self.context.run_dir))
        bash.check_output('cp {} {}'.format(config.ticks_csv, self.context.run_dir))
        bash.check_output('cp {} {}'.format(config.nodes_csv, self.context.run_dir))
        bash.check_output('cp {} {}'.format(config.args_csv, self.context.run_dir))
        logging.info('Simulation directory created')


def start_node(node, timeout=HTTP_TIMEOUT, height=0):
    node.run()
    node.connect_to_rpc(timeout)
    node.wait_until_rpc_ready()
    wait_until_height_reached(node, height)


def start_proxy_node(node, start_hash, normal_node):
    node.run(start_hash)
    node.wait_for_highest_tip_of_node(normal_node)


def transfer_coinbase_tx_to_normal_tx(node):
    node.set_spent_to_address()
    node.create_tx_chains()
    node.transfer_coinbases_to_normal_tx()
    logging.info("Transferred all coinbase-tx to normal tx for node={}".format(node.name))


def connect(node):
    node.connect()


def add_latency(node, zones):
    node.add_latency(zones)


def rm_node(node):
    node.delete_peers_file()
    node.rm()


def remove_old_containers_if_exists():
    containers = bash.check_output(dockercmd.ps_containers())
    if len(containers) > 0:
        bash.check_output(dockercmd.remove_all_containers(), lvl=logging.DEBUG)
        logging.info('Old containers removed')


def recreate_network():
    exit_code = bash.call_silent(dockercmd.inspect_network())
    if exit_code == 0:
        bash.check_output(dockercmd.rm_network())
    bash.check_output(dockercmd.create_network())
    logging.info('Docker network {} created'.format(config.network_name))


def wait_until_height_reached(node, height):
    while int(node.execute_cli('getblockcount')) < height:
        logging.debug('Waiting until node={} reached height={}...'.format(node.name, str(height)))
        utils.sleep(0.2)

def wait_until_height_reached_cli(node, height):
    msg = bash.check_output(
        "docker exec simcoin-{} sh -c '"
        "  while "
        "    [[ "
        "      $(bitcoin-cli "
        "        -regtest "
        "        --conf=/data/bitcoin.conf "
        "        getblockcount) -le {} "
        "    ]]; "
        "    do sleep 0.2; "
        "done; "
        "echo Block Height reached'".format(node.name, str(height)))
    logging.debug('Waiting until {}'.format(str(msg)))


def calc_number_of_tx_chains(txs_per_tick, blocks_per_tick, number_of_nodes):
    txs_per_block = txs_per_tick / blocks_per_tick
    txs_per_block_per_node = txs_per_block / number_of_nodes

    # 10 times + 3 chains in reserve
    needed_tx_chains = (txs_per_block_per_node / config.max_in_mempool_ancestors) * 10 + 3

    return math.ceil(needed_tx_chains)
