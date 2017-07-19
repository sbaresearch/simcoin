import dockercmd
import bitcoincmd
import proxycmd
import config
import tccmd
import bash
import utils
import logging
from datetime import datetime
import re


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def rm(self):
        return bash.check_output(dockercmd.rm_container(self.name))

    def rm_silent(self):
        return bash.call_silent(dockercmd.rm_container(self.name))


class PublicNode:
    def __init__(self):
        self.outgoing_ips = []
        self.latency = -1


class BitcoinNode(Node):
    log_file = bitcoincmd.guest_dir + '/regtest/debug.log'

    def __init__(self, name, ip):
        super().__init__(name, ip)
        self.name = name
        self.ip = ip
        self.mined_blocks = 0

    def run(self):
        return bash.check_output(bitcoincmd.start(self))

    def delete_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self.name))

    def connect(self, ips):
        for ip in ips:
            bash.check_output(bitcoincmd.connect(self.name, ip))

    def generate_tx(self):
        address = bash.check_output(bitcoincmd.get_new_address(self.name))
        return bash.check_output(bitcoincmd.send_to_address(self.name, address, 0.1))

    def set_tx_fee_as_low_as_possible(self):
        return bash.check_output(bitcoincmd.set_tx_fee_as_low_as_possible(self.name))

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
    matched = re.match(config.log_timestamp_regex, line)
    return datetime.strptime(matched.group(0), config.log_time_format).timestamp()


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self)

    def add_latency(self):
        return bash.check_output(tccmd.add(self.name, self.latency))


class SelfishPrivateNode(BitcoinNode):
    def __init__(self, name, ip):
        super().__init__(name, ip)


class ProxyNode(Node, PublicNode):
    log_file = '/tmp/selfish_proxy.log'

    def __init__(self, name, ip, private_ip, args):
        Node.__init__(self, name, ip)
        PublicNode.__init__(self)
        self.private_ip = private_ip
        self.args = args

    def run(self, start_hash):
        return bash.check_output(proxycmd.run_proxy(self, start_hash))

    def wait_for_highest_tip_of_node(self, node):
        block_hash = bash.check_output(bitcoincmd.get_best_block_hash(node.name))
        while block_hash != bash.check_output(proxycmd.get_best_public_block_hash(self.name)):
            utils.sleep(0.2)
            logging.debug('Waiting for  blocks to spread...')

    def cat_log_cmd(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(ProxyNode.log_file))

    def grep_log_for_errors(self):
        return bash.check_output(dockercmd.exec_cmd(self.name, config.log_error_grep.format(ProxyNode.log_file)))

    def add_latency(self):
        for cmd in tccmd.add_except_ip(self.name, self.latency, self.private_ip):
            bash.check_output(cmd)
