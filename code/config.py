import time

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"

network_name = 'simcoin-network'
node_image = 'btn/base:v3'
prefix = 'simcoin-'
selfish_node_image = 'proxy'
node_prefix = 'node-'
node_name = node_prefix + '{}.{}'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'
selfish_node_name = selfish_node_prefix + '{}'
selfish_node_proxy_name = selfish_node_name + selfish_node_proxy_postfix

data_dir = '../data/'
sim_dir = '{}run-{}/'.format(data_dir, time.time())
network_csv = data_dir + 'network.csv'
ticks_csv = data_dir + 'ticks.csv'
nodes_json = data_dir + 'nodes.json'
aggregated_log = data_dir + sim_dir + 'aggregated.log'
aggregated_sim_log = data_dir + sim_dir + 'aggregated_simulation.log'
log_file = data_dir + 'debug.log'
tmp_log = data_dir + sim_dir + 'tmp.log'
blocks_csv = data_dir + sim_dir + 'blocks.csv'
chains_csv = data_dir + sim_dir + 'chains.csv'
consensus_chain_csv = data_dir + sim_dir + 'consensus_chain.csv'
nodes_csv = data_dir + sim_dir + 'nodes.csv'
tx_csv = data_dir + sim_dir + 'tx.csv'

rpc_user = 'admin'
rpc_password = 'admin'
rpc_port = 18332


def create_rpc_connection_string(ip):
    return 'http://{}:{}@{}:{}'.format(rpc_user, rpc_password, ip, rpc_port)

reference_node = 'node-0'

warmup_blocks = 100
start_blocks_per_node = 2

log_prefix_timestamp = r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6})'
log_prefix_full = log_prefix_timestamp + ' ([a-zA-Z0-9]+-[0-9]+) '
log_error_grep = 'grep -E -i "WARN|FATAL|ERROR|CRITICAL|EXCEPTION" {} || true'
log_time_format = '%Y-%m-%d %H:%M:%S.%f'
log_line_sim_start = 'SIMULATION START'
log_line_sim_end = 'SIMULATION END'

bitcoin_data_dir = '/data'
bitcoin_regtest_dir = '/regtest'
client_dir = bitcoin_data_dir + bitcoin_regtest_dir


def host_dir(node):
    return sim_dir + node.name + bitcoin_regtest_dir
