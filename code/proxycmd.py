import dockercmd


def run_proxy(node, latency):
        public_ips = [str(ip) for ip in node.public_ips]
        args = '{} '.format(node.args) if node.args else ''
        proxy_cmd = 'python main.py ' + args + '--ips-public ' + ' '.join(public_ips)

        return '; ' .join([dockercmd.slow_network_proxy(latency, node.private_ip), proxy_cmd])
