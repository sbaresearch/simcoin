def run_proxy(node):
        public_ips = [str(ip) for ip in node.public_ips]
        args = '{} '.format(node.args) if node.args else ''
        return 'python main.py ' + args + '--ips-public ' + ' '.join(public_ips)
