import dockercmd
import bitcoincmd
import proxycmd
import config
import tccmd
import bash
import utils
import logging
from node.abstract import BitcoinNode
from node.abstract import PublicNode
from node.abstract import Node


class SelfishPrivateNode(BitcoinNode):
    def __init__(self, name, ip):
        super().__init__(name, ip)


class ProxyNode(Node, PublicNode):
    log_file = '/tmp/selfish_proxy.log'

    def __init__(self, name, ip, private_ip, args, latency):
        Node.__init__(self, name, ip)
        PublicNode.__init__(self, latency)
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

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)
