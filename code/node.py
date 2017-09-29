from cmd import dockercmd
from cmd import bitcoincmd
import config
import bash
from bitcoinrpc.authproxy import AuthServiceProxy
import logging
from cmd import tccmd
from cmd import proxycmd
import utils
import errno
from collections import OrderedDict
from collections import namedtuple
from bitcoin.wallet import CBitcoinSecret
from bitcoinrpc.authproxy import JSONRPCException
from bitcoin.core import lx, b2x, COutPoint, CMutableTxOut, CMutableTxIn, \
    CMutableTransaction, Hash160
from bitcoin.core.script import CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY,\
    OP_CHECKSIG, SignatureHash, SIGHASH_ALL
from bitcoin.wallet import CBitcoinAddress
from http.client import CannotSendRequest
from bitcoinrpc.authproxy import HTTP_TIMEOUT


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

    def run(self):
        bash.check_output(bitcoincmd.start(self, self.path))
        # sleep small amount to avoid
        # 'CannotSendRequest: Request-sent'
        # in bitcoinrpc
        utils.sleep(0.2)

    def is_running(self):
        return bash.check_output(
            dockercmd.check_if_running(
                self.name
            )
        ) == 'true'

    def rm(self):
        if self.is_running():
            try:
                self.execute_cli('stop')
            except Exception as error:
                logging.debug(
                    "Could not stop container {} with error={}"
                        .format(self.name, error)
                )
        while self.is_running():

            utils.sleep(1)
            logging.debug(
                'Wait until container {} stops'
                .format(self.name)
            )
        super(BitcoinNode, self).rm()

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
            except JSONRPCException as exce:
                logging.debug(
                    'Exception="{}" while calling RPC. '
                    'Waiting until RPC of node={} is ready.'
                    .format(exce, self.name)
                )
                utils.sleep(1)

    def connect_to_rpc(self, timeout=HTTP_TIMEOUT):
        self.rpc_connection = AuthServiceProxy(
            config.create_rpc_connection_string(self.ip),
            timeout=timeout
        )

    def delete_peers_file(self):
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
                method_to_call = getattr(self.rpc_connection, args[0])

                return method_to_call(*args[1:])
            except IOError as error:
                retry -= 1
                self.connect_to_rpc()
                logging.warning(
                    'Node={} could not execute RPC-call={} '
                    'because of error="{}". '
                    ' Reconnecting RPC and retrying.'
                    .format(self.name, args[0], error)
                )
            except CannotSendRequest as exce:
                retry -= 1
                self.connect_to_rpc(10)
                logging.warning(
                    'Node={} could not execute RPC-call={} '
                    'because of an CannotSendRequest exception with'
                    ' error="{}".'
                    ' Reconnecting RPC and retrying.'
                    .format(self.name, args[0], getmembers(exce))
                )

        logging.error(
            'Could not execute RPC-call={} on node {}'
            .format(args[0], self.name)
        )
        exit(-1)

    def grep_log_for_errors(self):
        return bash.check_output_without_log(
            config.log_error_grep.format(
                self.get_log_file()
            )
        )

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
                    (tx_chain.address, tx_chain.amount / 100000000),
                    (self.spent_to.address, tx_chain.amount / 100000000)
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

    def connect(self):
        for ip in self.outgoing_ips:
            self.execute_rpc('addnode', str(ip), 'add')


class SelfishPrivateNode(BitcoinNode):
    def __init__(self, name, group, ip, docker_image, path):
        super().__init__(name, group, ip, docker_image, path)


class ProxyNode(Node, PublicNode):
    log_file = '/tmp/selfish_proxy.log'

    def __init__(self, name, group, ip, private_ip, args, latency, docker_image):
        Node.__init__(self, name, group, ip, docker_image)
        PublicNode.__init__(self, latency)
        self.private_ip = private_ip
        self.args = args

    def run(self, start_hash):
        return bash.check_output(proxycmd.run_proxy(self, start_hash))

    def wait_for_highest_tip_of_node(self, node):
        block_hash = node.execute_rpc('getbestblockhash')
        utils.sleep(1)
        cmd = proxycmd.get_best_public_block_hash(self.name)
        while block_hash != bash.check_output(cmd):
            utils.sleep(1)
            logging.debug('Waiting for  blocks to spread...')

    def grep_log_for_errors(self):
        # TODO consider to implement this
        return 'Not yet implemented'

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
