import utils
import json
import config
from node.bitcoinnode import BitcoinNodeConfig
from node.selfishnode import SelfishNodeConfig
from node import bitcoinnode
from node import selfishnode


def create():
    nodes = []

    add_nodes = True
    while add_nodes:
        node_type = utils.get_node_type('Which node type do you want configure?\n> ')

        nodes.extend(node_types[node_type]())

        add_nodes = utils.get_boolean('Do you want to add another node type?\n> ')

        if add_nodes is False:
            check = check_if_share_sum_is_1(nodes)
            if check is False:
                print('Starting from scratch!')
                nodes = []
                add_nodes = True

    print('Creating {}...'.format(config.nodes_config_json))

    with open(config.nodes_config_json, 'w') as file:
        file.write(json.dumps([node.__dict__ for node in nodes], indent=4))


def read():
    with open(config.nodes_config_json) as data_file:
        nodes = json.load(data_file, object_hook=object_decoder)
    return nodes


def check_if_share_sum_is_1(nodes):
    sum_of_shares = 0
    for node in nodes:
        sum_of_shares += node.share
    sum_of_shares = round(sum_of_shares, 2)
    if sum_of_shares != 1:
        print('Sum of shares should be 1. It was {} instead.'.format(sum_of_shares))
        return False
    else:
        return True

node_types = {
    'bitcoin': bitcoinnode.create_bitcoin_config,
    'selfish': selfishnode.create_selfish_config,
}


def object_decoder(obj):
    if '__type__' in obj and obj['__type__'] == BitcoinNodeConfig.__name__:
        return BitcoinNodeConfig(obj['name'], obj['share'], obj['latency'])
    if '__type__' in obj and obj['__type__'] == SelfishNodeConfig.__name__:
        return SelfishNodeConfig(obj['name'], obj['share'], obj['latency'])
    raise Exception('Unknown node type')
