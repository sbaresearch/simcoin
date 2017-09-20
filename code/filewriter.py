import config
import logging
import time
from parse import BlockEvent
from clistats import Tip
import utils
from runner import StepTimes


class FileWriter:
    def __init__(self, context):
        self.context = context
        self.args = utils.read_json_file(config.args_json)

    def execute(self):
        utils.write_csv(self.context.path.blocks_csv, BlockEvent.csv_header, self.context.parsed_blocks.values(), self.args.tag)
        utils.write_csv(self.context.path.tips_csv, Tip.csv_header, self.context.tips, self.args.tag)

        self.context.step_times.append(StepTimes(time.time(), 'postprocessing_end'))
        utils.write_csv(self.context.path.step_times, StepTimes.csv_header(), self.context.step_times, self.args.tag)

        logging.info('Executed analyzer')

