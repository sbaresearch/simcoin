import config
import logging
import csv
import json
import time
from parse import ReceivedEvent
from parse import BlockEvent
from parse import TxEvent
from parse import ExceptionEvent
from parse import TickEvent
from parse import RPCExceptionEvent
from clistats import Tip
import utils


class FileWriter:
    def __init__(self, context):
        self.context = context
        self.args = utils.read_json_file(config.args_json)

    def execute(self):
        self.write_csv(config.blocks_csv, BlockEvent.csv_header(), self.context.parsed_blocks.values())
        self.write_csv(config.txs_csv, TxEvent.csv_header(), self.context.parsed_txs.values())
        self.write_csv(config.tx_exceptions_csv, ExceptionEvent.csv_header(), self.context.tx_exceptions)
        self.write_csv(config.block_exceptions_csv, ExceptionEvent.csv_header(), self.context.block_exceptions)
        self.write_csv(config.tick_infos_csv, TickEvent.csv_header(), self.context.tick_infos)
        self.write_csv(config.rpc_exceptions_csv, RPCExceptionEvent.csv_header(), self.context.rpc_exceptions)
        self.write_csv(config.blocks_received_csv, ReceivedEvent.csv_header(), self.context.blocks_received)
        self.write_csv(config.txs_received_csv, ReceivedEvent.csv_header(), self.context.txs_received)
        self.write_csv(config.tips_csv, Tip.csv_header(), self.context.tips)

        self.create_general_infos_json()

        logging.info('Executed analyzer')

    def create_general_infos_json(self):
        self.context.general_infos['step_times']['postprocessing_end'] = time.time()
        with open(config.general_infos_json, 'w') as file:
            file.write('{}\n'.format(json.dumps(self.context.general_infos)))

    def write_csv(self, file, header, elements):
        with open(file, 'w') as file:
            w = csv.writer(file, delimiter=';')
            header.append('tag')
            w.writerow(header)

            for element in elements:
                row = element.vars_to_array()
                row.append(self.args.tag)
                w.writerow(row)
