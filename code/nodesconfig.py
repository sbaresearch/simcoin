import utils
import json
import config


def create(create_all):
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
        file.write(json.dumps(nodes, indent=4))

    if create_all:
        pass


def create_normal_node_config():
    amount = utils.get_non_negative_int('How many normal nodes do you want create?\n> ')
    nodes = []

    for i in range(amount):
        node = {'type': 'normal'}

        print('{}. Node'.format(i+1))
        latency = utils.get_non_negative_int('What should be the latency of this node? [ms]\n> ')
        node['latency'] = latency

        share = utils.get_percentage('What should be the computational share? [0,1]\n> ')
        node['share'] = share

        nodes.append(node)

    return nodes


def check_if_share_sum_is_1(nodes):
    sum_of_shares = 0
    for node in nodes:
        print(node)
        sum_of_shares += node['share']
    sum_of_shares = round(sum_of_shares, 2)
    if sum_of_shares != 1:
        print('Sum of shares should be 1. It was {} instead.'.format(sum_of_shares))
        return False
    else:
        return True

node_types = {
    'normal': create_normal_node_config
}

if __name__ == '__main__':
    create(False)
