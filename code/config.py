# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"

root_dir = '../data/'
aggregated_log_file = root_dir + 'log'

node_image = 'btn/base:v3'
selfish_node_image = 'proxy'
node_name = 'node-{}'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'
selfish_node_name = selfish_node_prefix + '{}'
selfish_node_proxy_name = selfish_node_name + selfish_node_proxy_postfix

network_config = 'network.config'
tick_csv = 'ticks.csv'
aggregated_log = root_dir + 'aggregated.log'
log_file = 'debug.log'
tmp_log = root_dir + 'tmp.log'
blocks_csv = root_dir + 'blocks.csv'
chains_csv = root_dir + 'chains.csv'
consensus_chain_csv = root_dir + 'consensus_chains.csv'

reference_node = 'node-0'

warmup_blocks = 100

log_timestamp_regex = r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6})'
log_error_grep = 'grep -E -i "WARN|FATAL|ERROR|CRITICAL|EXCEPTION" {} || true'


def host_dir(node):
    return root_dir + node.name
