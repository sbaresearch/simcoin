import logging
import csv
import fcntl
import config


class Writer:
    def __init__(self, tag):
        self.tag = tag

    def write_csv(self, file_name, header, elements):
        write_header_csv(file_name, header)
        self.append_csv(file_name, elements)

    def append_csv(self, file_name, elements):
        with open(config.postprocessing_dir + file_name, 'a') as file:
            logging.debug('Waiting for lock to write to file={}'.format(file_name))
            fcntl.flock(file, fcntl.LOCK_EX)
            logging.debug('Received lock for writing to file={}'.format(file_name))

            w = csv.writer(file)
            for element in elements:
                row = element.vars_to_array()
                row.append(self.tag)
                w.writerow(row)


def write_header_csv(file_name, header):
    with open(config.postprocessing_dir + file_name, 'w') as file:
        logging.debug('Waiting for lock to write to file={}'.format(file_name))
        fcntl.flock(file, fcntl.LOCK_EX)
        logging.debug('Received lock for writing to file={}'.format(file_name))

        w = csv.writer(file)
        w.writerow(header + ['tag'])
