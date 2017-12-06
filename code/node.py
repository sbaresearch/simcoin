from cmd import dockercmd
from cmd import bitcoincmd
import config
import bash
import logging
from cmd import tccmd
import utils
from collections import OrderedDict
from collections import namedtuple
from bitcoin.wallet import CBitcoinSecret
from bitcoin.core import lx, b2x, COutPoint, CMutableTxOut, CMutableTxIn, \
    CMutableTransaction, Hash160
from bitcoin.core.script import CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY,\
    OP_CHECKSIG, SignatureHash, SIGHASH_ALL
from bitcoin.wallet import CBitcoinAddress
from http.client import CannotSendRequest
from bitcoin.rpc import Proxy
from bitcoin.rpc import JSONRPCError
from bitcoin.rpc import DEFAULT_HTTP_TIMEOUT


class Node:
    __slots__ = ['_name', '_ip', '_docker_image', '_group']

    def __init__(self, name, group, ip, docker_image):
        self._name = name
        self._ip = ip
        self._docker_image = docker_image
        self._group = group

    def rm(self):
        return bash.check_output(dockercmd.rm_container(self._name))

    @property
    def name(self):
        return self._name

    @property
    def ip(self):
        return self._ip


class BitcoinNode(Node):
    __slots__ = ['_path', '_spent_to', '_rpc_connection', '_current_tx_chain_index', '_tx_chains']

    def __init__(self, name, group, ip, docker_image, path):
        super().__init__(name, group, ip, docker_image)
        self._path = path
        self._spent_to = None
        self._rpc_connection = None
        self._current_tx_chain_index = 0
        self._tx_chains = []

    def create_conf_file(self):
        # file is needed for RPC connection
        with open(config.btc_conf_file.format(self.name), 'w') as file:
            file.write('rpcconnect={}\n'.format(self._ip))
            file.write('rpcport={}\n'.format(config.rpc_port))
            file.write('rpcuser={}\n'.format(config.rpc_user))
            file.write('rpcpassword={}\n'.format(config.rpc_password))

    def run(self, connect_to_ips):
        bash.check_output(bitcoincmd.start(self._name, str(self._ip), self._docker_image, self._path, connect_to_ips))

        # sleep small amount to avoid 'CannotSendRequest: Request-sent' in bitcoin.rpc
        utils.sleep(0.2)

    def is_running(self):
        return bash.check_output(
            dockercmd.check_if_running(
                self._name
            )
        ) == 'true'

    def close_rpc_connection(self):
        if self._rpc_connection is not None:
            self._rpc_connection.__dict__['_BaseProxy__conn'].close()
            logging.debug('Closed rpc connection to node={}'.format(self._name))

    def stop(self):
        self.execute_rpc('stop')
        logging.info('Send stop to node={}'.format(self.name))

    def get_log_file(self):
        return self._path + config.bitcoin_log_file_name

    def wait_until_rpc_ready(self):
        while True:
            try:
                bash.check_output(
                    "nc -z -w1 {} {}"
                    .format(self._ip, config.rpc_port)
                )
                break
            except Exception:
                logging.debug("Waiting with netcat until port is open")

        while True:
            try:
                self.execute_rpc('getnetworkinfo')
                break
            except JSONRPCError as exce:
                logging.debug('Waiting until RPC of node={} is ready.'.format(self._name))
                utils.sleep(1)

    def connect_to_rpc(self):
        self._rpc_connection = Proxy(
            btc_conf_file=config.btc_conf_file.format(self.name),
            timeout=config.rpc_simulation_timeout
        )

    def rm_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self._name))

    def execute_rpc(self, *args):
        retry = 30
        while retry > 0:
            try:
                return self._rpc_connection.call(args[0], *args[1:])
            except (IOError, CannotSendRequest) as error:
                logging.exception('Could not execute RPC-call={} on node={} because of error={}.'
                                  ' Reconnecting and retrying, {} retries left'
                                  .format(args[0], self._name,  error, retry))
                retry -= 1
                self.connect_to_rpc()
        raise Exception('Could not execute RPC-call={} on node {}'.format(args[0], self._name))

    def transfer_coinbases_to_normal_tx(self):
        for tx_chain in self._tx_chains:
            tx_chain.amount /= 2
            tx_chain.amount -= int(config.transaction_fee / 2)
            raw_transaction = self.execute_rpc(
                'createrawtransaction',
                [{
                    'txid': tx_chain.current_unspent_tx,
                    'vout': 0,
                }],
                OrderedDict([
                    (tx_chain.address, str(tx_chain.amount / 100000000)),
                    (self._spent_to.address, str(tx_chain.amount / 100000000))
                ])
            )
            signed_raw_transaction = self.execute_rpc(
                'signrawtransaction', raw_transaction
            )['hex']
            tx_chain.current_unspent_tx = self.execute_rpc(
                'sendrawtransaction',
                signed_raw_transaction
            )

    def generate_blocks(self, amount=1):
        logging.debug('{} trying to generate block'.format(self._name))
        block_hash = self.execute_rpc('generate', amount)
        logging.info('{} generated block with hash={}'.format(self._name, block_hash))

    def generate_tx(self):
        tx_chain = self.get_next_tx_chain()
        txid = lx(tx_chain.current_unspent_tx)
        txins = [
            CMutableTxIn(COutPoint(txid, 0)),
            CMutableTxIn(COutPoint(txid, 1))
        ]
        txin_seckeys = [tx_chain.seckey, self._spent_to.seckey]

        amount_in = tx_chain.amount
        tx_chain.amount -= int(config.transaction_fee / 2)

        txout1 = CMutableTxOut(
            tx_chain.amount,
            CBitcoinAddress(tx_chain.address).to_scriptPubKey()
        )
        txout2 = CMutableTxOut(
            tx_chain.amount,
            CBitcoinAddress(self._spent_to.address).to_scriptPubKey()
        )

        tx = CMutableTransaction(txins, [txout1, txout2], nVersion=2)

        for i, txin in enumerate(txins):
            txin_scriptPubKey = CScript([
                OP_DUP,
                OP_HASH160,
                Hash160(txin_seckeys[i].pub),
                OP_EQUALVERIFY,
                OP_CHECKSIG
            ])
            sighash = SignatureHash(txin_scriptPubKey, tx, i, SIGHASH_ALL)
            sig = txin_seckeys[i].sign(sighash) + bytes([SIGHASH_ALL])
            txin.scriptSig = CScript([sig, txin_seckeys[i].pub])

        tx_serialized = tx.serialize()
        logging.debug(
            '{} trying to sendrawtransaction'
            ' (in=2x{} out=2x{} fee={} bytes={})'
            ' using tx_chain number={}'
            .format(self._name,
                    amount_in,
                    txout1.nValue,
                    (amount_in * 2) - (txout1.nValue * 2),
                    len(tx_serialized),
                    self._current_tx_chain_index)
        )
        tx_hash = self.execute_rpc('sendrawtransaction', b2x(tx_serialized))
        tx_chain.current_unspent_tx = tx_hash
        logging.info(
            '{} sendrawtransaction was successful; tx got hash={}'
            .format(self._name, tx_hash)
        )

    def generate_spent_to_address(self):
        address = self.execute_rpc('getnewaddress')
        seckey = CBitcoinSecret(self.execute_rpc('dumpprivkey', address))
        self._spent_to = SpentToAddress(address, seckey)

    def create_tx_chains(self):
        for unspent_tx in self.execute_rpc('listunspent'):
            seckey = CBitcoinSecret(
                self.execute_rpc('dumpprivkey', unspent_tx['address'])
            )
            tx_chain = TxChain(
                unspent_tx['txid'],
                unspent_tx['address'],
                seckey,
                unspent_tx['amount'] * 100000000
            )

            self._tx_chains.append(tx_chain)

    def get_next_tx_chain(self):
        tx_chain = self._tx_chains[self._current_tx_chain_index]
        self._current_tx_chain_index = (
            (self._current_tx_chain_index + 1) %
            len(self._tx_chains)
        )

        return tx_chain


class PublicBitcoinNode(BitcoinNode):
    __slots__ = ['_latency', '_outgoing_ips']

    def __init__(self, name, group, ip, latency, docker_image, path):
        BitcoinNode.__init__(self, name, group, ip, docker_image, path)
        self._latency = latency
        self._outgoing_ips = []

    def set_outgoing_ips(self, outgoing_ips):
        self._outgoing_ips = outgoing_ips

    def add_latency(self, zones):
        for cmd in tccmd.create(self._name, zones, self._latency):
            bash.check_output(cmd)

    def run(self, connect_to_ips=None):
        if connect_to_ips is None:
            connect_to_ips = self._outgoing_ips

        super(PublicBitcoinNode, self).run(connect_to_ips)


class TxChain:
    __slots__ = ['_current_unspent_tx', '_address', '_seckey', '_amount']

    def __init__(self, current_unspent_tx, address, seckey, amount):
        self._current_unspent_tx = current_unspent_tx
        self._address = address
        self._seckey = seckey
        self._amount = amount

    @property
    def current_unspent_tx(self):
        return self._current_unspent_tx

    @current_unspent_tx.setter
    def current_unspent_tx(self, unspent_tx):
        self._current_unspent_tx = unspent_tx

    @property
    def address(self):
        return self._address

    @property
    def seckey(self):
        return self._seckey

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, amount):
        self._amount = amount


SpentToAddress = namedtuple('SpentToAddress', 'address seckey')


def create_conf_file(node):
    node.create_conf_file()


def start_node(node, height=0, connect_to_ips=None):
    node.run(connect_to_ips)
    node.connect_to_rpc()
    node.wait_until_rpc_ready()
    wait_until_height_reached(node, height)


def wait_until_height_reached(node, height):
    while int(node.execute_rpc('getblockcount')) < height:
        logging.debug('Waiting until node={} reached height={}...'.format(node.name, str(height)))
        utils.sleep(0.2)


def transfer_coinbase_tx_to_normal_tx(node):
    node.generate_spent_to_address()
    node.create_tx_chains()
    node.transfer_coinbases_to_normal_tx()
    logging.info("Transferred all coinbase-tx to normal tx for node={}".format(node.name))


def add_latency(node, zones):
    node.add_latency(zones)


def wait_until_node_stopped(node):
    parts = 10
    step = config.max_wait_time_bitcoin_runs_out / parts
    for i in range(parts):
        utils.sleep(step)
        logging.info('Wait until node={} runs out'.format(node.name))
        if node.is_running() is False:
            return
    logging.warning('Node={} did not stopped running'.format(node.name))


def rm_peers_file(node):
    node.rm_peers_file()


def graceful_rm(pool, nodes):
    pool.map(stop_node, nodes)
    pool.map(wait_until_node_stopped, nodes)
    pool.map(rm_node, nodes)


def stop_node(node):
    node.close_rpc_connection()
    node.stop()


def rm_node(node):
    node.rm()
