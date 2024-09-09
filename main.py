#!/usr/bin/python3
import re

import click
import docker
from docker.errors import APIError

from event import is_start, is_die, get_container_name, get_container_ip
from host import build_hosts_pattern, build_network_name, build_container_aliases, insert_on_hosts, remove_from_hosts


@click.command()
@click.option('-d', '--domain_name', default='.dnr', help='Domain name(default=.dnr)')
def main(
        domain_name: str,
):
    client = docker.from_env()
    hosts_path = ['./hosts']
    network_bridge = client.api.inspect_network('bridge')
    dnr_network_name = build_network_name(domain_name)

    try:
        client.api.create_network(dnr_network_name, check_duplicate=True)
    except APIError:
        pass  # Network already exists

    escaped_domain_name = re.escape(domain_name)
    pattern = re.compile(r'^.*' + escaped_domain_name + r'.*$')
    remove_from_hosts(pattern, hosts_path)
    for container_info in network_bridge.get('Containers').values():
        container_ip = container_info.get('IPv4Address').split('/')[0]
        container_name = container_info.get('Name')
        insert_on_hosts(container_ip, container_name, domain_name, pattern, hosts_path)
        aliases = build_container_aliases(container_name, domain_name)
        try:
            client.api.connect_container_to_network(container_name, dnr_network_name, aliases=aliases)
        except APIError:
            pass  # Container already connected

    for event in client.events(decode=True):
        if is_start(event):
            network_bridge = client.api.inspect_network('bridge')
            container_ip = get_container_ip(event, network_bridge)
            container_name = get_container_name(event)
            aliases = build_container_aliases(container_name, domain_name)
            insert_on_hosts(container_ip, container_name, domain_name, pattern, hosts_path)
            try:
                client.api.connect_container_to_network(container_name, dnr_network_name, aliases=aliases)
            except APIError:
                pass  # Container already connected

        if is_die(event):
            container_name = get_container_name(event)
            pattern = build_hosts_pattern(container_name, escaped_domain_name)
            remove_from_hosts(pattern, hosts_path)
            try:
                client.api.disconnect_container_from_network(container_name, dnr_network_name)
            except APIError:
                pass  # Container already disconnected


if __name__ == '__main__':
    main()
