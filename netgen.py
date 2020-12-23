"""
Utility to assist in generating BOSH cloud-config network sections.
Some tooling (looking at you, Genesis!) do not allow lazy IP selection and instead
require explicitly defined networks, including reserved static IP addresses.
Additional annoyance is done by not paying attention to what addresses have already
been assigned, leading to confusion when deploying infrastructure.

Sample:
    subnets:
    - azs: [z1,z2,z3]
      range: 192.168.123.0/24
      dns: [192.168.5.1]
    networks:
    - name: jumpbox
      size: 2
      static: 1
    - name: vault
      size: 4
      static: 3

Generates the following cloud-config networks section:
    networks:
    - name: jumpbox
      subnets:
      - azs:
        - z1
        - z2
        - z3
        dns:
        - 192.168.5.1
        gateway: 192.168.123.1
        range: 192.168.123.0/24
        reserved:
        - 192.168.123.0 - 192.168.123.1
        - 192.168.123.4 - 192.168.123.255
        static:
        - 192.168.123.2
      type: manual
    - name: vault
      subnets:
      - azs:
        - z1
        - z2
        - z3
        dns:
        - 192.168.5.1
        gateway: 192.168.123.1
        range: 192.168.123.0/24
        reserved:
        - 192.168.123.0 - 192.168.123.3
        - 192.168.123.8 - 192.168.123.255
        static:
        - 192.168.123.4 - 192.168.123.6
      type: manual
"""


import netaddr
import yaml
import argparse
import sys


class Networks:
    def __init__(self, networks):
        self.networks = networks


class Network:
    def __init__(self, name, type, subnets):
        self.name = name
        self.type = type
        self.subnets = subnets


class Subnet:
    def __init__(self, azs, range, dns, reserved, gateway, static):
        self.azs = azs
        self.range = range
        self.dns = dns
        self.reserved = reserved
        self.gateway = gateway
        self.static = static


def prepare_subnet_lists(subnets):
    print(f"Pre-processing {len(subnets)} subnet(s):")
    for subnet in subnets:
        subnet_range = subnet['range']
        ip_network = netaddr.IPNetwork(subnet_range)
        ip_list = list(ip_network.iter_hosts())
        ip_list.sort()
        print(f"* Subnet {subnet_range} has {len(ip_list)} addresses.")

        # Patch up the gateway
        if 'gateway' not in subnet:
            subnet_gateway = ip_list.pop(0)     # We assume the gateway is 1st in the list
            subnet['gateway'] = subnet_gateway
            print(f"  Gateway calculated to be {subnet_gateway}")
        else:
            ip_list.remove(netaddr.IPAddress(subnet['gateway']))

        subnet['list'] = ip_list
        subnet['ip_network'] = ip_network


def pull_out_addresses(ip_list, net_size) -> [netaddr.IPAddress]:
    address_list = []
    while len(address_list) < net_size:
        address_list.append(ip_list.pop(0))
    return address_list


def format_subnet_range(start_address, end_address) -> str:
    if start_address == end_address:
        return f"{start_address}"
    elif start_address < end_address:
        return f"{start_address} - {end_address}"
    else:   # Just in case they get messed up...
        return f"{end_address} - {start_address}"


def build_subnets(subnets, net_size, net_static) -> [Subnet]:
    subnet_list = []
    for x in subnets:
        subnet_azs = x['azs']
        subnet_dns = x['dns']
        subnet_range = x['range']
        subnet_gateway = str(x['gateway'])

        addresses = pull_out_addresses(x['list'], net_size)
        first_address = addresses[0]
        last_address = addresses[-1]
        first_in_network = netaddr.IPAddress(x['ip_network'].first)
        last_in_network = netaddr.IPAddress(x['ip_network'].last)

        subnet_reserved = []
        if first_in_network < first_address:
            subnet_reserved.append(format_subnet_range(first_in_network, first_address-1))
        if last_in_network > last_address:
            subnet_reserved.append(format_subnet_range(last_address+1, last_in_network))

        subnet_static = []
        if net_static > 0:
            first_static = addresses[0]
            last_static = addresses[net_static-1]
            subnet_static.append(format_subnet_range(first_static, last_static))

        subnet_list.append(Subnet(azs=subnet_azs,
                                  range=subnet_range,
                                  dns=subnet_dns,
                                  reserved=subnet_reserved,
                                  gateway=subnet_gateway,
                                  static=subnet_static))
    return subnet_list


def load_networks(networks, subnets) -> [Network]:
    net_list = []
    print("Processing networks:")
    for entry in networks:
        net_name = entry['name']
        print(f"* Network '{net_name}'")
        if 'type' in entry:
            net_type = entry['type']
        else:
            net_type = 'manual'
        net_size = entry['size']
        net_static = entry['static']
        net_subnets = build_subnets(subnets, net_size, net_static)

        net_list.append(Network(name=net_name,
                                type=net_type,
                                subnets=net_subnets))
    return Networks(net_list)


def noop(self, *args, **kw):
    pass


class NoAliasDumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True


def main(config_file, output_stream):
    with open(config_file) as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
        config_subnets = data['subnets']
        config_networks = data['networks']

        prepare_subnet_lists(config_subnets)
        networks = load_networks(config_networks, config_subnets)

        # Prevent the '!!python/object'
        yaml.emitter.Emitter.process_tag = noop
        yaml.dump(networks,
                  stream=output_stream,
                  default_flow_style=False,
                  Dumper=NoAliasDumper)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--config", dest="config_file", default="config.yml",
                        type=str, help="configuration file to use")
    parser.add_argument("--output", dest="output_file",
                        type=str, help="configuration file to use")
    args = parser.parse_args()

    if args.output_file:
        with open(args.output_file, "w") as output:
            main(args.config_file, output)
    else:
        main(args.config_file, sys.stdout)
