import config
import logging
from clistats import Tip
import utils


class FileWriter:
    def __init__(self, context):
        self.context = context
        self.args = utils.read_json_file(config.args_json)

    def execute(self):
        utils.write_csv(self.context.path.tips_csv, Tip.csv_header, self.context.tips, self.args.tag)

        logging.info('Executed analyzer')

