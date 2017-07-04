import dockercmd
import bitcoincmd
import proxycmd
import config
import tccmd


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def rm(self):
        return dockercmd.rm_container(self.name)


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
        return dockercmd.run_node(self, bitcoincmd.start())

    def delete_peers_file(self):
        return bitcoincmd.rm_peers(self.name)

    def wait_for_highest_tip_of_node(self, node):
        highest_tip = bitcoincmd.get_best_block_hash(node.name)
        node_tip = bitcoincmd.get_best_block_hash(self.name)
        return 'while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' \
               'do echo Waiting for blocks to spread...; sleep 0.2; done'

    def connect(self, nodes):
        return bitcoincmd.connect(self.name, nodes)

    def generate_tx(self):
        create_address_cmd = 'fresh_address=$(' + bitcoincmd.get_new_address(self.name) + ')'
        create_tx_cmd = bitcoincmd.send_to_address(self.name, '$fresh_address', 0.1)
        return '; '.join([create_address_cmd, create_tx_cmd])

    def generate_block(self, amount=1):
        return bitcoincmd.generate_block(self.name, amount)

    def get_chain_tips(self):
        return bitcoincmd.get_chain_tips(self.name)

    def get_block_count(self):
        return bitcoincmd.get_block_count(self.name)

    def get_block_hash(self, height):
        return bitcoincmd.get_block_hash(self.name, height)

    def get_block(self, block_hash):
        return bitcoincmd.get_block(self.name, block_hash)

    def cat_log(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(BitcoinNode.log_file))

    def grep_log_for_errors(self):
        return dockercmd.exec_cmd(self.name, config.log_error_grep.format(BitcoinNode.log_file))


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self)

    def add_latency(self):
        return [dockercmd.exec_cmd(self.name, tccmd.add(self.latency))]


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
        return dockercmd.run_selfish_proxy(self, proxycmd.run_proxy(self, start_hash))

    def wait_for_highest_tip_of_node(self, node):
        current_best_block_hash_cmd = 'current_best=$(' + bitcoincmd.get_best_block_hash(node.name) + ')'
        wait_for_selfish_node_cmd = 'while [[ $current_best != $(' + proxycmd.get_best_public_block_hash(self.name) + \
                                    ') ]]; do echo Waiting for blocks to spread...; sleep 0.2; done'
        return '; '.join(['sleep 2', current_best_block_hash_cmd, wait_for_selfish_node_cmd])

    def cat_log(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(ProxyNode.log_file))

    def grep_log_for_errors(self):
        return dockercmd.exec_cmd(self.name, config.log_error_grep.format(ProxyNode.log_file))

    def add_latency(self):
        return [dockercmd.exec_cmd(self.name, cmd) for cmd in tccmd.add_except_ip(self.latency, self.private_ip)]
