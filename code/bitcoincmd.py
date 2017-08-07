import dockercmd
import config

daemon = 'bitcoind '
args = {
    'regtest':            '-regtest',  # activate regtest mode
    'datadir':            '-datadir=' + config.bitcoin_data_dir,  # change the datadir
    'debug':              '-debug',  # log all events
    'logips':             '-logips',  # enable ip loging
    'logtimemicros':      '-logtimemicros',  # add microseconds to logging flag: DEFAULT_LOGTIMEMICROS
    'listen':             '-listen',  # ensure listening even if 'connect' is given
    'listenonion':        '-listenonion=0',  # disable tor
    'onlynet':            '-onlynet=ipv4',  # disable ipv6
    'reindex':            '-reindex',

    # try to keep fees as low as possible
    'paytxfee':           '-paytxfee=0.00001',
    'mintxfee':           '-mintxfee=0.00000001',
    'minrelaytxfee':      '-minrelatxfee=0.00000001',
    'blockmintxfee':      '-blockmintxfee=0.00000001',
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
    return dockercmd.exec_cmd(node, 'rm -f {}/regtest/peers.dat'.format(config.bitcoin_data_dir))
