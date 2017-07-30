from stats import Stats
from parse import Parser
import parse


class PostProcessing:
    def __init__(self, executor):
        self.executor = executor

    def execute(self):
        stats = Stats(self.executor)
        stats.save_consensus_chain()
        stats.aggregate_logs()
        parser = Parser([node.name for node in self.executor.all_bitcoin_nodes.values()])
        parse.cut_log()
        parser.parse_aggregated_sim_log()
        parser.create_block_csv()
        parser.create_tx_csv()
        stats.save_chains()
        stats.node_stats()
