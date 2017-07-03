import logging
import os
import subprocess


def check_output_and_log(cmd):
    output = check_output(cmd)
    [logging.info(output.strip()) for output in output.splitlines()]


def check_output(cmd):
    logging.info(cmd)
    return_value = subprocess.check_output(cmd, shell=True, executable='/bin/bash')
    return return_value.decode('utf-8').rstrip()


def call(cmd):
    logging.info(cmd)
    return subprocess.call(cmd, shell=True, executable='/bin/bash')


def call_silent(cmd):
    logging.info(cmd)
    with open(os.devnull, 'w') as devnull:
        return subprocess.call(cmd, shell=True, executable='/bin/bash', stderr=devnull, stdout=devnull)
