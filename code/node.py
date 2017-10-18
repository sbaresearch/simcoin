from cmd import dockercmd
from cmd import bitcoincmd
import config
import bash
import logging
from cmd import tccmd
from cmd import proxycmd
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
import traceback


class Node:
    def __init__(self, name, group, ip, docker_image):
        self.name = name
        self.group = group
        self.ip = ip
        self.docker_image = docker_image

    def rm(self):
        return bash.check_output(dockercmd.rm_container(self.name))


class PublicNode:
    def __init__(self, latency):
        self.latency = latency
        self.outgoing_ips = []


class BitcoinNode(Node):
    def __init__(self, name, group, ip, docker_image, path):
        super().__init__(name, group, ip, docker_image)
        self.path = path
        self.spent_to = None
        self.rpc_connection = None
        self.current_tx_chain_index = 0
        self.tx_chains = []

    def run(self, connect_to_ips):
        bash.check_output(bitcoincmd.start(self, self.path, connect_to_ips))

        # sleep small amount to avoid 'CannotSendRequest: Request-sent' in bitcoin.rpc
        utils.sleep(0.2)

    def is_running(self):
        return bash.check_output(
            dockercmd.check_if_running(
                self.name
            )
        ) == 'true'

    def close_rpc_connection(self):
        if self.rpc_connection is not None:
            self.rpc_connection.__dict__['_BaseProxy__conn'].close()
            logging.debug('Closed rpc connection to node={}'.format(self.name))

    def stop(self):
        self.execute_rpc('stop')

    def get_log_file(self):
        return self.path + config.bitcoin_log_file_name

    def wait_until_rpc_ready(self):
        """ Block till port ready """
        while True:
            try:
                bash.check_output(
                    "nc -z -w1 {} {}"
                    .format(self.ip, config.rpc_port)
                )
                break
            except Exception:
                logging.debug("Waiting with netcat until port is open")

        while True:
            try:
                self.execute_rpc('getnetworkinfo')
                break
            except JSONRPCError as exce:
                logging.debug(
                    'Exception="{}" while calling RPC. '
                    'Waiting until RPC of node={} is ready.'
                    .format(exce, self.name)
                )
                utils.sleep(1)

    def connect_to_rpc(self, timeout=DEFAULT_HTTP_TIMEOUT):
        self.rpc_connection = Proxy(
            config.create_rpc_connection_string(self.ip),
            timeout=timeout
        )

    def rm_peers_file(self):
        return bash.check_output(bitcoincmd.rm_peers(self.name))

    def execute_cli(self, *args):
        return bash.check_output(
            "docker exec simcoin-{} bitcoin-cli "
            "-regtest "
            "-conf=/data/bitcoin.conf {}"
            .format(
              self.name,
              ' '.join(list(map(str, args)))
            )
        )

    def execute_rpc(self,  *args):
        retry = 30
        while retry >= 0:
            try:
                return self.rpc_connection.call(args[0], *args[1:])
            except IOError as error:
                retry -= 1
                self.connect_to_rpc()
                logging.warning('Could not execute RPC-call={} on node={} because of error={}.'
                                ' Reconnecting and retrying, {} retries left'
                                .format(args[0], self.name,  error, retry))
            except CannotSendRequest as exce:
                retry -= 1
                self.connect_to_rpc(10)
                logging.warning('Could not execute RPC-call={} on node={} because of error={}.'
                                ' Reconnecting and retrying, {} retries left'
                                .format(args[0], self.name,  exce, retry))
        logging.error('Could not execute RPC-call={} on node {}'.format(args[0], self.name))
        raise Exception('Could not execute RPC-call={} on node {}'.format(args[0], self.name))

    def transfer_coinbases_to_normal_tx(self):
        for tx_chain in self.tx_chains:
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
                    (self.spent_to.address, str(tx_chain.amount / 100000000))
                ])
            )
            signed_raw_transaction = self.execute_rpc(
                'signrawtransaction', raw_transaction
            )['hex']
            tx_chain.current_unspent_tx = self.execute_rpc(
                'sendrawtransaction',
                signed_raw_transaction
            )

    def generate_block(self):
        logging.debug('{} trying to generate block'.format(self.name))
        block_hash = self.execute_rpc('generate', 1)
        logging.info('{} generated block with hash={}'.format(self.name, block_hash))

    def generate_tx(self):
        tx_chain = self.get_next_tx_chain()
        txid = lx(tx_chain.current_unspent_tx)
        txins = [
            CMutableTxIn(COutPoint(txid, 0)),
            CMutableTxIn(COutPoint(txid, 1))
        ]
        txin_seckeys = [tx_chain.seckey, self.spent_to.seckey]

        amount_in = tx_chain.amount
        tx_chain.amount -= int(config.transaction_fee / 2)

        txout1 = CMutableTxOut(
            tx_chain.amount,
            CBitcoinAddress(tx_chain.address).to_scriptPubKey()
        )
        txout2 = CMutableTxOut(
            tx_chain.amount,
            CBitcoinAddress(self.spent_to.address).to_scriptPubKey()
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
            .format(self.name,
                    amount_in,
                    txout1.nValue,
                    (amount_in * 2) - (txout1.nValue * 2),
                    len(tx_serialized),
                    self.current_tx_chain_index)
        )
        tx_hash = self.execute_rpc('sendrawtransaction', b2x(tx_serialized))
        tx_chain.current_unspent_tx = tx_hash
        logging.info(
            '{} sendrawtransaction was successful; tx got hash={}'
            .format(self.name, tx_hash)
        )

    def set_spent_to_address(self):
        address = self.execute_rpc('getnewaddress')
        seckey = CBitcoinSecret(self.execute_rpc('dumpprivkey', address))
        self.spent_to = SpentToAddress(address, seckey)

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

            self.tx_chains.append(tx_chain)

    def get_next_tx_chain(self):
        tx_chain = self.tx_chains[self.current_tx_chain_index]
        self.current_tx_chain_index = ((self.current_tx_chain_index + 1) %
                                       len(self.tx_chains))

        return tx_chain


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, group, ip, latency, docker_image, path):
        BitcoinNode.__init__(self, name, group, ip, docker_image, path)
        PublicNode.__init__(self, latency)

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)

    def run(self, connect_to_ips=None):
        if connect_to_ips is None:
            connect_to_ips = self.outgoing_ips

        super(PublicBitcoinNode, self).run(connect_to_ips)


class SelfishPrivateNode(BitcoinNode):
    def __init__(self, name, group, ip, ip_proxy, docker_image, path):
        super().__init__(name, group, ip, docker_image, path)
        self.ip_proxy = ip_proxy

    def run(self, connect_to_ips=None):
        if connect_to_ips is None:
            connect_to_ips = [self.ip_proxy]

        super(SelfishPrivateNode, self).run(connect_to_ips)


class ProxyNode(Node, PublicNode):

    def __init__(self, name, group, ip, private_ip, args, latency, docker_image, path):
        Node.__init__(self, name, group, ip, docker_image)
        PublicNode.__init__(self, latency)
        self.private_ip = private_ip
        self.args = args
        self.path = path

    def run(self, start_hash):
        return bash.check_output(proxycmd.run_proxy(self, start_hash, self.path))

    def wait_for_highest_tip_of_node(self, node):
        block_hash = node.execute_rpc('getbestblockhash')
        utils.sleep(1)
        cmd = proxycmd.get_best_public_block_hash(self.name)
        while block_hash != bash.check_output(cmd):
            utils.sleep(1)
            logging.debug('Waiting for  blocks to spread...')

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)


class TxChain:
    def __init__(self, current_unspent_tx, address, seckey, amount):
        self.current_unspent_tx = current_unspent_tx
        self.address = address
        self.seckey = seckey
        self.amount = amount


SpentToAddress = namedtuple('SpentToAddress', 'address seckey')


def rm_peers_file(node):
    node.rm_peers_file()


def graceful_rm(pool, nodes):
    pool.map(stop_node, nodes)
    pool.map(wait_until_node_stopped, nodes)
    pool.map(rm_node, nodes)


def stop_node(node):
    node.close_rpc_connection()
    node.stop()
    logging.info('Send stop to node={}'.format(node.name))


def wait_until_node_stopped(node):
    parts = 10
    step = config.max_wait_time_bitcoin_runs_out / parts
    for i in range(parts):
        utils.sleep(step)
        logging.info('Wait until node={} runs out'.format(node.name))
        if node.is_running() is False:
            return
    logging.warning('Node={} did not stopped running'.format(node.name))


def rm_node(node):
    node.rm()
