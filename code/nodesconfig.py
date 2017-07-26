import json
import config
import argparse
import sys


node_groups = [
    {'argparse': '--node-group-a', 'variable': 'node_group_a', 'default': ['bitcoin', 10, 1, 200]},
    {'argparse': '--node-group-b', 'variable': 'node_group_b', 'default': None},
    ]


def parse():
    parser = argparse.ArgumentParser()

    for node_group in node_groups:
        parser.add_argument(node_group['argparse']
                            , default=node_group['default']
                            , nargs='+'
                            , help='{}. Pass [node_type] [amount] [share] [latency]'.format(node_group['variable'])
                            )

    args = parser.parse_args(sys.argv[2:])
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))
    return args


def create():
    args = parse()

    nodes = []
    for node_group in node_groups:
        node_args = getattr(args, node_group['variable'])
        if node_args:
            nodes.extend(create_node_group(node_args))

    check_if_share_sum_is_1(nodes)

    print('Creating {}...'.format(config.nodes_config_json))

    with open(config.nodes_config_json, 'w') as file:
        file.write(json.dumps([node.__dict__ for node in nodes], indent=4))


def read():
    with open(config.nodes_config_json) as data_file:
        nodes = json.load(data_file, object_hook=object_decoder)
    return nodes


def object_decoder(obj):
    return NodeConfig(obj['node_type'], obj['name'], obj['share'], obj['latency'])


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


def create_node_group(node_args):
    node_type = str(node_args[0])
    amount = int(node_args[1])
    share = float(node_args[2])
    latency = int(node_args[3])

    nodes = []
    for i in range(amount):
        nodes.append(NodeConfig(node_type, config.node_name.format(i + 1), share/amount, latency))
    return nodes


class NodeConfig:
    def __init__(self, node_type, name, share, latency):
        self.node_type = node_type
        self.name = name
        self.share = share
        self.latency = latency
