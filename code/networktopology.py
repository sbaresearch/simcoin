import argparse
import csv
import random
import pandas
import sys
import config

random.seed(1)


def check_positive(value):
    integer_value = int(value)
    if integer_value < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return integer_value


def check_percentage(value):
    float_value = float(value)
    if float_value < 0 or float_value > 1:
        raise argparse.ArgumentTypeError("%s is a percentage value and should be be in [0,1]" % value)
    return float_value

parser = argparse.ArgumentParser(description='Create a simple network.config for Bitcoin Network Simulator.')

parser.add_argument('--nodes'
                    , default=4
                    , type=check_positive
                    , help='Number of Bitcoin nodes.'
                    )

parser.add_argument('--selfish-nodes'
                    , default=1
                    , type=check_positive
                    , help='Number of selfish Bitcoin nodes.'
                    )

parser.add_argument('--latency'
                    , default=200
                    , type=check_positive
                    , help='Latency between nodes in milliseconds.'
                    )

parser.add_argument('--connectivity'
                    , default=.5
                    , type=check_percentage
                    , help='Connectivity between nodes.'
                    )


args = parser.parse_args()

print("arguments called with: {}".format(sys.argv))
print("parsed arguments: {}".format(args))

total_nodes = args.nodes + args.selfish_nodes
size_matrix = total_nodes + 1
nodes = args.nodes
selfish_nodes = args.selfish_nodes

header = ['']
header.extend([config.node_prefix + str(i) for i in range(nodes)])
header.extend([config.selfish_node_prefix + str(i) for i in range(selfish_nodes)])
matrix = [[] for i in range(size_matrix)]

for i in range(1, size_matrix):
    matrix[i] = [-1 for j in range(size_matrix)]
    matrix[i][0] = header[i]
matrix[0] = header

for i in range(1, size_matrix):
    for j in range(1, i):
        if random.random() < args.connectivity:
            matrix[i][j] = matrix[j][i] = args.latency
        else:
            matrix[i][j] = matrix[j][i] = -1

print(pandas.DataFrame(matrix))

with open(config.network_config, "w") as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerows([['nodes', args.nodes], ['selfish-nodes', args.selfish_nodes]])
    writer.writerows(matrix)
