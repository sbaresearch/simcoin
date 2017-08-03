import dockercmd
import bitcoincmd
import config
import bash
from datetime import datetime
import re
from bitcoinrpc.authproxy import AuthServiceProxy


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

    def execute_rpc(self,  *args):
        method_to_call = getattr(self.rpc_connection, args[0])
        return method_to_call(*args[1:])

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

    def generate_block_rpc(self, amount=1):
        return self.rpc_connection.generate(amount)

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
