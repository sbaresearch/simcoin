import dockercmd
import bitcoincmd
import config
import bash
from bitcoinrpc.authproxy import AuthServiceProxy
import logging
import tccmd
import proxycmd
import utils
import errno
from collections import OrderedDict


class Node:
    def __init__(self, name, ip, docker_image):
        self.name = name
        self.ip = ip
        self.docker_image = docker_image

    def rm(self):
        return bash.check_output(dockercmd.rm_container(self.name))

    def rm_silent(self):
        return bash.call_silent(dockercmd.rm_container(self.name))


class PublicNode:
    def __init__(self, latency):
        self.latency = latency
        self.outgoing_ips = []


class BitcoinNode(Node):
    log_file = config.client_dir + '/debug.log'

    def __init__(self, name, ip, docker_image):
        super().__init__(name, ip, docker_image)
        self.name = name
        self.ip = ip
        self.spent_to_address = None
        self.rpc_connection = None
        self.tx_chains = []

    def run(self):
        bash.check_output(bitcoincmd.start(self))
        self.connect_to_rpc()

    def connect_to_rpc(self):
        self.rpc_connection = AuthServiceProxy(config.create_rpc_connection_string(self.ip))

    def delete_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self.name))

    def execute_rpc(self,  *args):
        retry = 1
        while retry >= 0:
            try:
                method_to_call = getattr(self.rpc_connection, args[0])

                return method_to_call(*args[1:])
            except IOError as error:
                if error.errno == errno.EPIPE:
                    retry -= 1
                    self.connect_to_rpc()
                    logging.debug('Error={} occurred. Reconnecting RPC and retrying.'.format(error))

        logging.error("Could'nt execute rpc-call={} on node {}".format(args[0], self.name))
        exit(-1)

    def grep_log_for_errors(self):
        return bash.check_output(dockercmd.exec_cmd(self.name, config.log_error_grep.format(BitcoinNode.log_file)))

    def cat_log_cmd(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(BitcoinNode.log_file))

    def transfer_coinbases_to_normal_tx(self):
        for tx_chain in self.tx_chains:
            tx_chain.available_coins -= config.transaction_fee + config.smallest_amount
            raw_transaction = self.execute_rpc('createrawtransaction',
                                  [{
                                    'txid':    tx_chain.current_unspent_tx,
                                    'vout':    0,
                                  }],
                                  OrderedDict(
                                      [
                                          (tx_chain.address, tx_chain.available_coins/100000000),
                                          (self.spent_to_address, config.smallest_amount_btc)
                                      ])
                                  )
            signed_raw_transaction = self.execute_rpc('signrawtransaction', raw_transaction)['hex']
            tx_chain.current_unspent_tx = self.execute_rpc('sendrawtransaction', signed_raw_transaction)


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip, latency, docker_image):
        BitcoinNode.__init__(self, name, ip, docker_image)
        PublicNode.__init__(self, latency)

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)

    def connect(self):
        for ip in self.outgoing_ips:
            self.execute_rpc('addnode', str(ip), 'add')


class SelfishPrivateNode(BitcoinNode):
    def __init__(self, name, ip, docker_image):
        super().__init__(name, ip, docker_image)


class ProxyNode(Node, PublicNode):
    log_file = '/tmp/selfish_proxy.log'

    def __init__(self, name, ip, private_ip, args, latency, docker_image):
        Node.__init__(self, name, ip, docker_image)
        PublicNode.__init__(self, latency)
        self.private_ip = private_ip
        self.args = args

    def run(self, start_hash):
        return bash.check_output(proxycmd.run_proxy(self, start_hash))

    def wait_for_highest_tip_of_node(self, node):
        block_hash = node.execute_rpc('getbestblockhash')
        while block_hash != bash.check_output(proxycmd.get_best_public_block_hash(self.name)):
            utils.sleep(0.2)
            logging.debug('Waiting for  blocks to spread...')

    def cat_log_cmd(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(ProxyNode.log_file))

    def grep_log_for_errors(self):
        return bash.check_output(dockercmd.exec_cmd(self.name, config.log_error_grep.format(ProxyNode.log_file)))

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)


class TxChain:
    def __init__(self, current_unspent_tx, address, seckey):
        self.current_unspent_tx = current_unspent_tx
        self.address = address
        self.seckey = seckey
        self.available_coins = config.coinbase_amount
