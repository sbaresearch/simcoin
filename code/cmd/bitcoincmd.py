from cmd import dockercmd
import config

daemon = 'bitcoind '
args = {
    'regtest':            '-regtest',  # activate regtest mode
    'datadir':            '-datadir=' + config.bitcoin_data_dir,  # change the datadir
    'debug':              '-debug=cmpctblock -debug=net -debug=mempool',  # make sure bitcoind logs all needed events
    'logips':             '-logips',  # enable ip loging
    'logtimemicros':      '-logtimemicros',  # add microseconds to logging flag: DEFAULT_LOGTIMEMICROS

    'listen':             '-listen=1',
    'listenonion':        '-listenonion=0',  # disable tor
    'onlynet':            '-onlynet=ipv4',  # disable ipv6
    'dnsseed':            '-dnsseed=0',

    'reindex':            '-reindex',
    'checkmempool':       '-checkmempool=0',
    'keypool':            '-keypool=1',
}


def start(node, path, connect_to_ips):
    return_args = args.copy()
    cmd = transform_to_cmd(return_args)
    for ip in connect_to_ips:
        cmd += ' -connect=' + str(ip)
    return dockercmd.run_node(node, cmd, path)


def transform_to_cmd(args_to_transform):
    return daemon + ' '.join(args_to_transform.values())


def rm_peers(node):
    return dockercmd.exec_cmd(node, 'rm -f {}/regtest/peers.dat'.format(config.bitcoin_data_dir))
