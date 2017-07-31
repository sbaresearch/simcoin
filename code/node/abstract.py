import dockercmd
import bitcoincmd
import config
import bash
from datetime import datetime
import re
import utils
from bitcoinrpc.authproxy import AuthServiceProxy
import logging


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

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

    def __init__(self, name, ip):
        super().__init__(name, ip)
        self.name = name
        self.ip = ip
        self.spent_to_address = ''
        self.rpc_connection = None

    def run(self):
        return bash.check_output(bitcoincmd.start(self))

    def stop(self):
        return bash.check_output(bitcoincmd.stop(self.name))

    def delete_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self.name))

    def connect(self, ips):
        for ip in ips:
            bash.check_output(bitcoincmd.connect(self.name, ip))

    def rpc_connect(self):
        self.rpc_connection = AuthServiceProxy(config.create_rpc_connection_string(self.ip))

    def generate_tx(self, address):
        return bash.check_output(bitcoincmd.send_to_address(self.name, address, '0.001'))

    def generate_block_rpc(self, amount=1):
        return self.rpc_connection.generate(amount)

    def get_new_address(self):
        return bash.check_output(bitcoincmd.get_new_address(self.name))

    def list_unspent(self):
        return bash.check_output(bitcoincmd.list_unspent(self.name))

    def list_lock_unspent(self):
        return bash.check_output(bitcoincmd.list_lock_unspent(self.name))

    def get_balance(self):
        return bash.check_output(bitcoincmd.get_balance(self.name))

    def generate_block(self, amount=1):
        return bash.check_output(bitcoincmd.generate_block(self.name, amount))

    def get_chain_tips(self):
        return bash.check_output(bitcoincmd.get_chain_tips(self.name))

    def get_block_count(self):
        return bash.check_output(bitcoincmd.get_block_count(self.name))

    def get_block_hash(self, height):
        return bash.check_output(bitcoincmd.get_block_hash(self.name, height))

    def get_block_hash_silent(self, height):
        return bash.call_silent(bitcoincmd.get_block_hash(self.name, height))

    def get_block(self, block_hash):
        return bash.check_output(bitcoincmd.get_block(self.name, block_hash))

    def get_best_block_hash(self):
        return bash.check_output(bitcoincmd.get_best_block_hash(self.name))

    def grep_log_for_errors(self):
        return bash.check_output(dockercmd.exec_cmd(self.name, config.log_error_grep.format(BitcoinNode.log_file)))

    def cat_log_cmd(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(BitcoinNode.log_file))

    def tx_created(self, tx_hash):
        return get_timestamp(self.name, 'Relaying wtx {}'.format(tx_hash))

    def tx_received(self, tx_hash):
        return get_timestamp(self.name, 'accepted {}'.format(tx_hash))

    def block_is_new_tip(self, block_hash):
        return get_timestamp(self.name, 'best={}'.format(block_hash))


def get_timestamp(node_name, grep_cmd):
    cmd = dockercmd.exec_cmd(node_name, 'cat {} | grep "{}"'.format(BitcoinNode.log_file, grep_cmd))
    return_value = bash.call_silent(cmd)
    if return_value != 0:
        return -1
    line = bash.check_output(cmd)
    matched = re.match(config.log_prefix_timestamp, line)
    return datetime.strptime(matched.group(0), config.log_time_format).timestamp()


def create_config(node):
    latency = utils.get_non_negative_int('What should be the latency of this node? [ms]\n> ')
    node.latency = latency

    share = utils.get_percentage('What should be the computational share? [0,1]\n> ')
    node.share = share
    return node
