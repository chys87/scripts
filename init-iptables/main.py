#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys

import yaml


class Executor:
    def __init__(self, real):
        self._real = real

    def execute(self, *args):
        print(*args)
        if self._real:
            subprocess.check_call(args)

    def ipv4(self, *args):
        self.execute('iptables', *args)

    def ipv6(self, *args):
        self.execute('ip6tables', *args)

    def both(self, *args):
        self.ipv4(*args)
        self.ipv6(*args)


def _load_service_map():
    tcp = {}
    udp = {}
    content = open('/etc/services').read()
    for m in re.finditer(r'^(\w+)\s+(\d+)/(tcp|udp)\b', content, re.M):
        service, port, protocol = m.group(1, 2, 3)
        if protocol == 'tcp':
            tcp[service] = int(port)
        else:
            udp[service] = int(port)
    return tcp, udp


def _port_set_to_str(ports):
    parts = []
    current_lo = current_hi = None

    def commit():
        if current_lo is None:
            return
        elif current_lo == current_hi:
            parts.append(str(current_lo))
        else:
            parts.append('{}:{}'.format(current_lo, current_hi))

    for port in sorted(ports):
        if current_hi is not None and port == current_hi + 1:
            current_hi = port
        else:
            commit()
            current_lo = current_hi = port

    commit()

    return ','.join(parts)

def _run_protocol(ex, protocol, service_map, conf):
    if not conf:
        return

    accept_ports = set()
    drop_ports = set()
    default_drop = False

    for service, action in conf.items():
        if action == 'accept':
            dst = accept_ports
        elif action == 'drop':
            dst = drop_ports
        else:
            sys.exit('Unknown action: {}'.format(action))

        if service == 'default':
            default_drop = action == 'drop'
            continue

        if isinstance(service, int) or service.isdigit():
            ports = [int(service)]
        elif re.match(r'^\d+-\d+$', service):
            lo, hi = map(int, service.split('-'))
            ports = range(lo, hi + 1)
        else:
            try:
                ports = [service_map[service]]
            except KeyError:
                sys.exit('Unknown service: {}'.format(service))

        for port in ports:
            dst.add(port)

    if default_drop:
        if accept_ports:
            ex.both('-A', 'INPUT', '-p', protocol, '-m', 'multiport',
                    '--dports', _port_set_to_str(accept_ports), '-j', 'ACCEPT')
        ex.both('-A', 'INPUT', '-p', protocol, '-j', 'DROP')
    else:
        if drop_ports:
            ex.both('-A', 'INPUT', '-p', protocol, '-m', 'multiport',
                    '--dports', _port_set_to_str(drop_ports), '-j', 'DROP')


def main():
    parser = argparse.ArgumentParser(description='Initialize iptables')
    parser.add_argument('--notest', action='store_true')
    parser.add_argument('conf_file')
    args = parser.parse_args()

    conf = yaml.load(open(args.conf_file))

    ex = Executor(args.notest)

    # Clear old iptables
    ex.both('-F')
    ex.both('-X')

    # Accept established connections
    ex.both(*'-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT'.split())

    # Accept all local requests
    ex.ipv4(*'-A INPUT -i lo -s 127.0.0.1/8 -d 127.0.0.1/8 -j ACCEPT'.split())
    ex.ipv6(*'-A INPUT -i lo -s ::1 -d ::1 -j ACCEPT'.split())

    # Services
    tcp, udp = _load_service_map()

    _run_protocol(ex, 'tcp', tcp, conf.get('tcp'))
    _run_protocol(ex, 'udp', udp, conf.get('udp'))

    # Ping
    if conf.get('ping') == 'drop':
        ex.ipv4(*'-A INPUT -p icmp --icmp-type echo-request -j DROP'.split())
        ex.ipv6(*'-A INPUT -p icmpv6 --icmpv6-type echo-request -j DROP'
                .split())

if __name__ == '__main__':
    main()
