import json
import config
import argparse
import sys
import utils
import bash
from cmd import dockercmd

node_groups = [
        {'argparse': '--node-group-a', 'variable': 'node_group_a', 'default':
            ['bitcoin', 10, 1, 200, config.standard_image]},
        {'argparse': '--node-group-b', 'variable': 'node_group_b', 'default': None},
        {'argparse': '--node-group-c', 'variable': 'node_group_c', 'default': None},
        {'argparse': '--node-group-d', 'variable': 'node_group_d', 'default': None},
        {'argparse': '--node-group-e', 'variable': 'node_group_e', 'default': None},
    ]


def create_parser():
    parser = argparse.ArgumentParser()

    for node_group in node_groups:
        parser.add_argument(node_group['argparse']
                            , default=node_group['default']
                            , nargs='+'
                            , help='{}. Pass [node_type] [amount] [share] [latency] [docker-image]'.format(node_group['variable'])
                            )
    return parser


def create(unknown_arguments=False):
    print('Called nodes config')

    parser = create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}\n".format(args))
    utils.update_args_json(args)

    nodes = []
    for index, node_group in enumerate(node_groups):
        node_args = getattr(args, node_group['variable'])
        if node_args:
            if len(node_args) != 5:
                parser.exit(-1, 'Pass [node_type] [amount] [share] [latency] [docker-image] for {}\n'
                            .format(node_group['variable']))
            check_if_image_exists(node_args)

            nodes.extend(create_node_group(node_args, index + 1))

    check_if_share_sum_is_1(nodes)

    print('Created {}:'.format(config.nodes_json))
    print(json.dumps([node.__dict__ for node in nodes], indent=4))

    with open(config.nodes_json, 'w') as file:
        file.write(json.dumps([node.__dict__ for node in nodes], indent=4))
    print('End nodes config\n\n')


def read():
    utils.check_for_file(config.nodes_json)
    with open(config.nodes_json) as data_file:
        nodes = json.load(data_file, object_hook=object_decoder)
    return nodes


def object_decoder(obj):
    return NodeConfig(obj['node_type'], obj['name'], obj['share'], obj['latency'], obj['docker_image'])


def check_if_image_exists(node_args):
    docker_image = str(node_args[4])

    return_value = bash.call_silent(dockercmd.inspect_image(docker_image))
    if return_value != 0:
        print("Image {} doesn't exist. Check `docker images` for available images and"
              " consult the Makefile for how wo create the image.".format(docker_image))
        exit(-1)


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


def create_node_group(node_args, index):
    node_type = str(node_args[0])
    amount = int(node_args[1])
    share = float(node_args[2])
    latency = int(node_args[3])
    docker_image = str(node_args[4])

    nodes = []
    for i in range(amount):
        nodes.append(NodeConfig(node_type, config.node_name.format(index, i + 1), share/amount, latency, docker_image))
    return nodes


class NodeConfig:
    def __init__(self, node_type, name, share, latency, docker_image):
        self.node_type = node_type
        self.name = name
        self.share = share
        self.latency = latency
        self.docker_image = docker_image
