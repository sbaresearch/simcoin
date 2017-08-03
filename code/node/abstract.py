import dockercmd
import bitcoincmd
import config
import bash
from datetime import datetime
import re
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
        bash.check_output(bitcoincmd.start(self))
        self.rpc_connection = AuthServiceProxy(config.create_rpc_connection_string(self.ip))

    def delete_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self.name))

    def execute_rpc(self,  *args):
        method_to_call = getattr(self.rpc_connection, args[0])

        logging.info('{} {}'.format(self.name, args))
        return_value = method_to_call(*args[1:])
        logging.info(return_value)

        return return_value

    def grep_log_for_errors(self):
        return bash.check_output(dockercmd.exec_cmd(self.name, config.log_error_grep.format(BitcoinNode.log_file)))

    def cat_log_cmd(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(BitcoinNode.log_file))
