import dockercmd
import bitcoindcmd
import proxycmd
import config


class Node:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def rm(self):
        return dockercmd.rm_container(self.name)


class PublicNode:
    def __init__(self):
        self.outgoing_ips = []


class BitcoindNode(Node):
    def __init__(self, name, ip):
        super().__init__(name, ip)
        self.name = name
        self.ip = ip

    def run(self):
        return dockercmd.run_node(self, bitcoindcmd.start_user())

    def delete_peers_file(self):
        return bitcoindcmd.rm_peers(self.name)

    def wait_for_highest_tip_of_node(self, node):
        node_tip = bitcoindcmd.get_best_block_hash(node.name)
        highest_tip = bitcoindcmd.get_best_block_hash(self.name)
        return 'while [[ $(' + highest_tip + ') != $(' + node_tip + ') ]]; ' \
               'do echo Waiting for blocks to spread...; sleep 0.2; done'

    def connect(self, nodes):
        return bitcoindcmd.connect(self.name, nodes)

    def wait_until_height_reached(self, height):
        height_cmd = bitcoindcmd.get_block_count(self.name)
        return 'while [[ $(' + height_cmd + ') < ' + str(height) + ' ]]; ' \
               'do echo Waiting until height=' + str(height) + ' is reached...; sleep 0.2; done'

    def generate_tx(self):
        create_address_cmd = 'fresh_address=$(' + bitcoindcmd.get_new_address(self.name) + ')'
        create_tx_cmd = bitcoindcmd.send_to_address(self.name, '$fresh_address', 0.1)
        return '; '.join([create_address_cmd, create_tx_cmd])


class PublicBitcoindNode(BitcoindNode, PublicNode):
    def __init__(self, name, ip):
        BitcoindNode.__init__(self, name, ip)


class SelfishPrivateNode(BitcoindNode):
    def __init__(self, name, ip):
        super().__init__(name, ip)


class ProxyNode(Node, PublicNode):
    def __init__(self, name, ip, private_ip, args):
        Node.__init__(self, name, ip)
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
