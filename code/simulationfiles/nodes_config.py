import json
import config
import argparse
import sys
import utils
import bash
from cmd import dockercmd
import logging
import csv
from collections import namedtuple

node_groups = [
        {'argparse': '--group-a', 'variable': 'group_a', 'default':
            ['bitcoin', 10, 1, 200, config.standard_image]},
        {'argparse': '--group-b', 'variable': 'group_b', 'default': None},
        {'argparse': '--group-c', 'variable': 'group_c', 'default': None},
        {'argparse': '--group-d', 'variable': 'group_d', 'default': None},
        {'argparse': '--group-e', 'variable': 'group_e', 'default': None},
    ]


def create_parser():
    parser = argparse.ArgumentParser()

    for node_group in node_groups:
        parser.add_argument(node_group['argparse']
                            , default=node_group['default']
                            , nargs='+'
                            , help='{}. Pass [node_type] [amount] [share] [latency] [docker-image]'
                                   .format(node_group['variable'])
                            )
    return parser


def create(unknown_arguments=False):
    logging.info('Called nodes config')

    parser = create_parser()
    if unknown_arguments:
        args = parser.parse_known_args(sys.argv[2:])[0]
    else:
        args = parser.parse_args(sys.argv[2:])
    logging.info("Parsed arguments in {}: {}".format(__name__, args))
    utils.update_args(args)

    nodes = []
    for index, node_group in enumerate(node_groups):
        node_args = getattr(args, node_group['variable'])
        if node_args:
            if len(node_args) != 5:
                parser.exit(-1, 'Pass [node_type] [amount] [share] [latency] [docker-image] for {}\n'
                            .format(node_group['variable']))
            check_if_image_exists(node_args)

            nodes.extend(create_node_group(node_args, node_group['variable'], index + 1))

    check_if_share_sum_is_1(nodes)

    logging.info('Created {}:'.format(config.nodes_csv))
    print(json.dumps([node for node in nodes], indent=4))

    with open(config.nodes_csv, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['node_type', 'group', 'name', 'share', 'latency', 'docker_image'])
        writer.writerows(
            [[node.node_type, node.group, node.name, node.share, node.latency, node.docker_image] for node in nodes])
    logging.info('End nodes config')


def check_if_image_exists(node_args):
    docker_image = str(node_args[4])

    return_value = bash.call_silent(dockercmd.inspect(docker_image))
    if return_value != 0:
        logging.error("Image {} doesn't exist. Check `docker images` for available images and"
                      " consult the Makefile for how wo create the image.".format(docker_image))
        exit(-1)


def check_if_share_sum_is_1(nodes):
    sum_of_shares = 0
    for node in nodes:
        sum_of_shares += node.share
    sum_of_shares = round(sum_of_shares, 2)
    if sum_of_shares != 1:
        logging.error('Sum of shares should be 1. It was {} instead.'.format(sum_of_shares))
        exit(-1)


def create_node_group(node_args, group, index):
    node_type = str(node_args[0])
    amount = int(node_args[1])
    share = float(node_args[2])
    latency = int(node_args[3])
    docker_image = str(node_args[4])

    nodes = []
    for i in range(amount):
        nodes.append(NodeConfig(node_type, group, config.node_name.format(index, i + 1), share/amount, latency, docker_image))
    return nodes


NodeConfig = namedtuple('NodeConfig', 'node_type group name share latency docker_image')
