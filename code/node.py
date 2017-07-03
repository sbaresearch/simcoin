import dockercmd
import bitcoindcmd
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


class BitcoindNode(Node):
    log_file = bitcoindcmd.guest_dir + '/regtest/debug.log'

    def __init__(self, name, ip):
        super().__init__(name, ip)
        self.name = name
        self.ip = ip

    def run(self):
        return dockercmd.run_node(self, bitcoindcmd.start_user())

    def delete_peers_file(self):
        return bitcoindcmd.rm_peers(self.name)

    def wait_for_highest_tip_of_node(self, node):
        highest_tip = bitcoindcmd.get_best_block_hash(node.name)
        node_tip = bitcoindcmd.get_best_block_hash(self.name)
        return 'while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' \
               'do echo Waiting for blocks to spread...; sleep 0.2; done'

    def connect(self, nodes):
        return bitcoindcmd.connect(self.name, nodes)

    def generate_tx(self):
        create_address_cmd = 'fresh_address=$(' + bitcoindcmd.get_new_address(self.name) + ')'
        create_tx_cmd = bitcoindcmd.send_to_address(self.name, '$fresh_address', 0.1)
        return '; '.join([create_address_cmd, create_tx_cmd])

    def generate_block(self, amount=1):
        return bitcoindcmd.generate_block(self.name, amount)

    def get_block_count(self):
        return bitcoindcmd.get_block_count(self.name)

    def get_block_hash(self, height):
            return bitcoindcmd.get_block_hash(self.name, height)

    def cat_log(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(BitcoindNode.log_file))

    def grep_log_for_errors(self):
        return dockercmd.exec_cmd(self.name, config.log_error_grep.format(BitcoindNode.log_file))


class PublicBitcoindNode(BitcoindNode, PublicNode):
    def __init__(self, name, ip):
        BitcoindNode.__init__(self, name, ip)
        PublicNode.__init__(self)

    def add_latency(self):
        return [dockercmd.exec_cmd(self.name, tccmd.add(self.latency))]


class SelfishPrivateNode(BitcoindNode):
    def __init__(self, name, ip):
        super().__init__(name, ip)


class ProxyNode(Node, PublicNode):
    log_file = '/tmp/selfish_proxy.log'

    def __init__(self, name, ip, private_ip, args):
        Node.__init__(self, name, ip)
        PublicNode.__init__(self)
        self.private_ip = private_ip
        self.args = args

    def run(self):
        current_best_block_hash_cmd = 'start_hash=$(' + bitcoindcmd.get_best_block_hash(config.reference_node) + ')'
        run_cmd = dockercmd.run_selfish_proxy(self, proxycmd.run_proxy(self, '$start_hash'))
        return '; '.join([current_best_block_hash_cmd, run_cmd])

    def wait_for_highest_tip_of_node(self, node):
        current_best_block_hash_cmd = 'current_best=$(' + bitcoindcmd.get_best_block_hash(node.name) + ')'
        wait_for_selfish_node_cmd = 'while [[ $current_best != $(' + proxycmd.get_best_public_block_hash(self.name) + \
                                    ') ]]; do echo Waiting for blocks to spread...; sleep 0.2; done'
        return '; '.join(['sleep 2', current_best_block_hash_cmd, wait_for_selfish_node_cmd])

    def cat_log(self):
        return dockercmd.exec_cmd(self.name, 'cat {}'.format(ProxyNode.log_file))

    def grep_log_for_errors(self):
        return dockercmd.exec_cmd(self.name, config.log_error_grep.format(ProxyNode.log_file))

    def add_latency(self):
        return [dockercmd.exec_cmd(self.name, cmd) for cmd in tccmd.add_except_ip(self.latency, self.private_ip)]
