import plan


def start(strategy='default'):
    daemon = ' bitcoind '
    default = {
          'regtest': ' -regtest ',             # activate regtest mode
          'datadir': ' -datadir=' + plan.guest_dir + ' ',       # change the datadir
          'debug': ' -debug ',                 # log all events
          # 'printblocktree': ' -printblocktree', # removed (would print tree on startup)
          # 'printtoconsole': ' -printtoconsole ', # print the log to stdout instead of a file
          'logips': ' -logips ',               # enable ip loging
          'logtimemicros': ' -logtimemicros',  # add microseconds to logging flag: DEFAULT_LOGTIMEMICROS
          'listen' : ' -listen ',              # ensure listening even if 'connect' is given
          'listenonion' : ' -listenonion=0 ',  # disable tor
          'onlynet': ' -onlynet=ipv4 ',        # disable ipv6
    }
    configs = {
        'default': {},
        'bootstrap' : {
            'disablewallet': ' -disablewallet=1 ' # disable wallet
        },
        'user': {
            'dnsseed' : ' -dnsseed=0 ',  # disable dns seed lookups, otherwise this gets seeds even with docker --internal network
            'addnode' : ' -addnode=' + plan.ip_bootstrap + ' ', # only connect ourself introductionary node
            'seednode': ' -seednode=240.0.0.3 ',
            'keypool' : ' -keypool=1 '
        },
        'miner-solo' : {
            'addnode' : ' -addnode=fst ', # only connect to ourself introductionary node
            'keypool' : ' -keypool=1 '
        }
    }
    default.update(configs[strategy])
    return daemon + (' '.join(default.values()))


def info():
    return [
        #        'getconnectioncount',
        #        'getblockcount',
        #        'getinfo',
        #        'getmininginfo',
                'getpeerinfo'
    ]
