import config
import dockercmd

daemon = 'bitcoind '
guest_dir = '/data'
args = {
    'regtest':            '-regtest',  # activate regtest mode
    'datadir':            '-datadir=' + guest_dir,  # change the datadir
    'debug':              '-debug',  # log all events
    # 'printblocktree':     '-printblocktree', # removed (would print tree on startup)
    # 'printtoconsole':     '-printtoconsole', # print the log to stdout instead of a file
    'logips':             '-logips',  # enable ip loging
    'logtimemicros':      '-logtimemicros',  # add microseconds to logging flag: DEFAULT_LOGTIMEMICROS
    'listen':             '-listen',  # ensure listening even if 'connect' is given
    'listenonion':        '-listenonion=0',  # disable tor
    'onlynet':            '-onlynet=ipv4',  # disable ipv6
    'reindex':            '-reindex',
}


def start(node):
    specific_args = {
        'dnsseed':          '-dnsseed=0',  # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
        'keypool':          '-keypool=1'
    }
    return_args = args.copy()
    return_args.update(specific_args)
    return dockercmd.run_node(node, transform_to_cmd(return_args))


def start_selfish_mining():
    specific_args = {
        'keypool':          '-keypool=1',
        'dnsseed':          '-dnsseed=0',
    }
    return_args = args.copy()
    return_args.update(specific_args)
    return_args.pop('listen', None)
    return transform_to_cmd(return_args)


def transform_to_cmd(args_to_transform):
    return daemon + ' '.join(args_to_transform.values())


def rm_peers(node):
    return dockercmd.exec_cmd(node, 'rm -f {}/regtest/peers.dat'.format(guest_dir))


def get_best_block_hash(node):
    return exec_cli(node, 'getbestblockhash')


def generate_block(node, amount=1):
    return exec_cli(node, 'generate {}'.format(amount))


def get_new_address(node):
    return exec_cli(node, 'getnewaddress')


def list_lock_unspent(node):
    return exec_cli(node, 'listlockunspent')


def list_unspent(node):
    return exec_cli(node, 'listunspent')


def send_to_address(node, address, amount):
    return exec_cli(node, 'sendtoaddress ' + address + ' ' + str(amount))


def get_balance(node):
    return exec_cli(node, 'getbalance')


def get_chain_tips(node):
    return exec_cli(node, 'getchaintips')


def get_block_count(node):
    return exec_cli(node, 'getblockcount')


def get_peer_info(node):
    return exec_cli(node, 'getpeerinfo')


def get_block_hash(node, height):
    return exec_cli(node, 'getblockhash ' + str(height))


def get_block(node, block_hash):
    return exec_cli(node, 'getblock ' + block_hash)


def set_tx_fee_as_low_as_possible(node):
    return exec_cli(node, 'settxfee 0.00000001')


def connect(node, ip):
    return exec_cli(node, 'addnode ' + ip + ' add')


def exec_cli(node, command):
    return dockercmd.exec_cmd(node,
                              'bitcoin-cli'
                              ' -regtest'
                              ' -datadir=' + guest_dir +
                              ' ' + command)
