import plan
import dockercmd

daemon = ' bitcoind '
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
}


def start():
    return transform_to_cmd(args)


def start_selfish_mining(node):
    specific_args = {
        'keypool':          '-keypool=1',
        'addnode':          '-addnode=' + str(node.ip),
        'dnsseed':          '-dnsseed=0',
    }
    args.update(specific_args)
    args.pop('listen', None)
    return transform_to_cmd(args)


def start_user():
    specific_args = {
        'dnsseed':          '-dnsseed=0',  # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
        'addnode':          '-addnode=' + plan.ip_bootstrap,  # only connect ourself introductionary node
        'keypool':          '-keypool=1'
    }
    args.update(specific_args)
    return transform_to_cmd(args)


def start_bootstrap():
    specific_args = {
        'disablewallet':    '-disablewallet=1'  # disable wallet
    }
    args.update(specific_args)
    return transform_to_cmd(args)


def transform_to_cmd(args_to_transform):
    return daemon + ' '.join(args_to_transform.values())


def info():
    return [
        # 'getconnectioncount',
        # 'getblockcount',
        # 'getinfo',
        # 'getmininginfo',
        'getpeerinfo'
    ]


def get_best_block_hash(node):
    return exec_bitcoin_cli(node, 'getbestblockhash')


def generate_block(node, amount=1):
    return exec_bitcoin_cli(node, 'generate {}'.format(amount))


def get_new_address(node):
    return exec_bitcoin_cli(node, 'getnewaddress')


def send_to_address(node, address, amount):
    return exec_bitcoin_cli(node, 'sendtoaddress ' + address + ' ' + str(amount))


def get_chain_tips(node):
    return exec_bitcoin_cli(node, 'getchaintips > ' + guest_dir + '/chaintips.json')


def exec_bitcoin_cli(node, command):
    return dockercmd.exec_bash(node,
                               'bitcoin-cli'
                               ' -regtest'
                               ' -datadir=' + guest_dir +
                               ' ' + command
                               )
