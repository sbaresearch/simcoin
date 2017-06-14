# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"

root_dir = '$PWD/../data/'
aggregated_log_file = root_dir + 'log'

node_image = 'btn/base:v3'
selfish_node_image = 'proxy'
node_prefix = 'node-'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'

network_config = 'network.config'
tick_csv = 'ticks.csv'

blocks_to_make_coinbase_spendable = 100


def host_dir(node):
    return root_dir + node.name
