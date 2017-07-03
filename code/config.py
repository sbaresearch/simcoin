import time

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"

out_dir = 'out'
sim_dir = '{}/run-{}/'.format(out_dir, time.time())
aggregated_log_file = sim_dir + 'log'

network_name = 'simcoin-network'
node_image = 'btn/base:v3'
prefix = 'simcoin-'
selfish_node_image = 'proxy'
node_prefix = 'node-'
node_name = node_prefix + '{}'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'
selfish_node_name = selfish_node_prefix + '{}'
selfish_node_proxy_name = selfish_node_name + selfish_node_proxy_postfix

network_config = 'network.csv'
tick_csv = 'ticks.csv'
aggregated_log = sim_dir + 'aggregated.log'
log_file = 'debug.log'
tmp_log = sim_dir + 'tmp.log'
blocks_csv = sim_dir + 'blocks.csv'
chains_csv = sim_dir + 'chains.csv'
consensus_chain_csv = sim_dir + 'consensus_chains.csv'

reference_node = 'node-0'

warmup_blocks = 100

log_timestamp_regex = r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6})'
log_error_grep = 'grep -E -i "WARN|FATAL|ERROR|CRITICAL|EXCEPTION" {} || true'


def host_dir(node):
    return sim_dir + node.name
