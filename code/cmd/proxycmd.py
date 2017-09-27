from cmd import dockercmd


def run_proxy(node, start_hash):
    args = '{} '.format(node.args) if node.args else ''
    return dockercmd.run_selfish_proxy(node, 'python main.py {} --ip-private {} --ips-public {} --start-hash {}'
                                       .format(args, str(node.private_ip), ' '.join(node.outgoing_ips), start_hash))


def get_best_public_block_hash(node):
    return exec_cli(node, 'get_best_public_block_hash')


def start_hash(node):
    return exec_cli(node, 'start_hash')


def exec_cli(node, cmd):
    return dockercmd.exec_cmd(node, 'python cli.py {}'.format(cmd))
