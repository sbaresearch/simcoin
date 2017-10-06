from cmd import dockercmd
import config

daemon = 'bitcoind '
args = {
    'regtest':            '-regtest',
    'datadir':            '-datadir=' + config.bitcoin_data_dir,

    # log all events relevant for parsing
    'debug':              '-debug=cmpctblock -debug=net -debug=mempool',
    'logips':             '-logips',
    'logtimemicros':      '-logtimemicros',


    # activate listen even though explicit -connect will be set
    'listen':             '-listen=1',
    'listenonion':        '-listenonion=0',
    'onlynet':            '-onlynet=ipv4',
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
