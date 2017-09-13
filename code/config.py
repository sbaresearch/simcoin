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

rpc_user = 'admin'
rpc_password = 'admin'
rpc_port = 18332
rpc_simulation_timeout = 0.25


def create_rpc_connection_string(ip):
    return 'http://{}:{}@{}:{}'.format(rpc_user, rpc_password, ip, rpc_port)


reference_node = 'node-0'

blocks_needed_to_make_coinbase_spendable = 100
max_in_mempool_ancestors = 25

log_prefix_timestamp = r'^([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{6})'
log_prefix_full = log_prefix_timestamp + ' ([a-zA-Z0-9-\.]+) [0-9]+ '
log_error_grep = 'grep -E -i "WARN|FATAL|ERROR|CRITICAL|EXCEPTION" {} || true'
log_time_format = '%Y-%m-%d %H:%M:%S.%f'
log_line_sim_start = 'SIMULATION START'
log_line_sim_end = 'SIMULATION END'

smallest_amount = 1
smallest_amount_btc = 0.00000001
transaction_fee = 1000

data_dir = '../data/'
log_file = data_dir + 'debug.log'
soft_link_to_sim_dir = '{}last_run'.format(data_dir)

network_csv_file_name = 'network.csv'
ticks_csv_file_name = 'ticks.csv'
nodes_json_file_name = 'nodes.json'
args_json_file_name = 'args.json'

network_csv = data_dir + network_csv_file_name
ticks_csv = data_dir + ticks_csv_file_name
nodes_json = data_dir + nodes_json_file_name
args_json = data_dir + args_json_file_name

bitcoin_data_dir = '/data'
bitcoin_regtest_dir = '/regtest'
client_dir = bitcoin_data_dir + bitcoin_regtest_dir


class Path:
    def __init__(self):
        self.sim_dir = '{}run-{}/'.format(data_dir, time.time())

        self.aggregated_log = self.sim_dir + 'aggregated.log'
        self.aggregated_sim_log = self.sim_dir + 'aggregated_simulation.log'

        self.postprocessing_dir = self.sim_dir + 'postprocessing/'

        self.general_infos_json = self.postprocessing_dir + 'general_infos.json'
        self.tmp_log = self.postprocessing_dir + 'tmp.log'
        self.blocks_csv = self.postprocessing_dir + 'blocks.csv'
        self.tips_csv = self.postprocessing_dir + 'tips.csv'
        self.txs_csv = self.postprocessing_dir + 'txs.csv'
        self.tx_exceptions_csv = self.postprocessing_dir + 'tx_exceptions.csv'
        self.block_exceptions_csv = self.postprocessing_dir + 'block_exceptions.csv'
        self.rpc_exceptions_csv = self.postprocessing_dir + 'rpc_exceptions.csv'
        self.mempool_snapshots_csv = self.postprocessing_dir + 'mempool_snapshots.csv'
        self.blocks_received_csv = self.postprocessing_dir + 'blocks_received.csv'
        self.txs_received_csv = self.postprocessing_dir + 'txs_received.csv'
        self.tick_infos_csv = self.postprocessing_dir + 'tick_infos.csv'
        self.log_errors_txt = self.postprocessing_dir + 'log_errors.txt'
        self.cpu_time_csv = self.postprocessing_dir + 'cpu_time.csv'
        self.memory_csv = self.postprocessing_dir + 'memory.csv'

    def client_dir_on_host(self, name):
        return self.sim_dir + name + bitcoin_regtest_dir

