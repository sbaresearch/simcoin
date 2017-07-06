import logging
import os
import subprocess


def check_output(cmd, lvl=logging.INFO):
    logging.info(cmd)
    output = subprocess.check_output(cmd, shell=True, executable='/bin/bash')
    encoded_output = output.decode('utf-8').rstrip()
    for line in encoded_output.splitlines():
        logging.log(lvl, line.strip())
    return encoded_output


def call_silent(cmd):
    logging.info(cmd)
    with open(os.devnull, 'w') as devnull:
        return subprocess.call(cmd, shell=True, executable='/bin/bash', stderr=devnull, stdout=devnull)
