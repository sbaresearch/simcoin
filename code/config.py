import time

# IP range from RFC6890 - IP range for future use
# it does not conflict with https://github.com/bitcoin/bitcoin/blob/master/src/netbase.h
ip_range = "240.0.0.0/4"
ip_zones = '240.{}.0.0/16'

standard_image = 'simcoin/normal:v3'

network_name = 'simcoin-network'
prefix = 'simcoin-'
node_prefix = 'node-'
node_name = node_prefix + '{}.{}'
selfish_node_prefix = 'selfish-node-'
selfish_node_proxy_postfix = '-proxy'
selfish_node_name = selfish_node_prefix + '{}'
selfish_node_proxy_name = selfish_node_name + selfish_node_proxy_postfix

data_dir = '../data/'
sim_dir = '{}run-{}/'.format(data_dir, time.time())
soft_link_to_sim_dir = '{}last_run'.format(data_dir)
network_csv_file_name = 'network.csv'
ticks_csv_file_name = 'ticks.csv'
nodes_json_file_name = 'nodes.json'
args_json_file_name = 'args.json'
network_csv = data_dir + network_csv_file_name
ticks_csv = data_dir + ticks_csv_file_name
nodes_json = data_dir + nodes_json_file_name
args_json = data_dir + args_json_file_name
aggregated_log = data_dir + sim_dir + 'aggregated.log'
aggregated_sim_log = data_dir + sim_dir + 'aggregated_simulation.log'
log_file = data_dir + 'debug.log'
tmp_log = data_dir + sim_dir + 'tmp.log'
blocks_csv = data_dir + sim_dir + 'blocks.csv'
chains_csv = data_dir + sim_dir + 'chains.csv'
consensus_chain_csv = data_dir + sim_dir + 'consensus_chain.csv'
nodes_csv = data_dir + sim_dir + 'nodes.csv'
txs_csv = data_dir + sim_dir + 'txs.csv'
tx_exceptions_csv = data_dir + sim_dir + 'tx_exceptions.csv'
mempool_snapshots_csv = data_dir + sim_dir + 'mempool_snapshots.csv'

rpc_user = 'admin'
rpc_password = 'admin'
rpc_port = 18332


def create_rpc_connection_string(ip):
    return 'http://{}:{}@{}:{}'.format(rpc_user, rpc_password, ip, rpc_port)

reference_node = 'node-0'

blocks_needed_to_make_coinbase_spendable = 100
max_in_mempool_ancestors = 25

log_prefix_timestamp = r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6})'
log_prefix_full = log_prefix_timestamp + ' ([a-zA-Z0-9-\.]+) '
log_error_grep = 'grep -E -i "WARN|FATAL|ERROR|CRITICAL|EXCEPTION" {} || true'
log_time_format = '%Y-%m-%d %H:%M:%S.%f'
log_line_sim_start = 'SIMULATION START'
log_line_sim_end = 'SIMULATION END'

bitcoin_data_dir = '/data'
bitcoin_regtest_dir = '/regtest'
client_dir = bitcoin_data_dir + bitcoin_regtest_dir


def host_dir(node):
    return sim_dir + node.name + bitcoin_regtest_dir


smallest_amount = 1
smallest_amount_btc = 0.00000001
coinbase_amount = 5000000000
transaction_fee = 1000
