#!/usr/bin/python3
import re
import sys
import traceback

import click
import docker
import logging
from docker.errors import APIError

from event import is_start, is_die, get_container_name, get_container_ip
from host import build_hosts_pattern, build_network_name, build_container_aliases, insert_on_hosts, remove_from_hosts


@click.command()
@click.option('-d', '--domain_name', default='.dnr', help='Domain name(default=.dnr)')
@click.option('-v', '--verbose', 'is_verbose', is_flag=True, default=False, help='Logging verbosity')
def main(
        domain_name: str,
        is_verbose: bool,
):
    logging_level = logging.INFO if is_verbose else logging.ERROR
    logging.basicConfig(stream=sys.stdout, level=logging_level, format='[%(level)s] %(message)s')
    logging.info('Starting')
    client = docker.from_env()
    hosts_path = './hosts'
    network_bridge = client.api.inspect_network('bridge')
    dnr_network_name = build_network_name(domain_name)
    try:
        client.api.create_network(dnr_network_name, check_duplicate=True)
        logging.info(f'Network {dnr_network_name} created')
    except APIError:
        logging.warning(f'Network {dnr_network_name} already exists')

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
            logging.info(f'Container {container_name} connected to {dnr_network_name}')
        except APIError:
            logging.warning(f'Container {container_name} already connected tp {dnr_network_name}')

    for event in client.events(decode=True):
        if is_start(event):
            network_bridge = client.api.inspect_network('bridge')
            container_ip = get_container_ip(event, network_bridge)
            container_name = get_container_name(event)
            aliases = build_container_aliases(container_name, domain_name)
            insert_on_hosts(container_ip, container_name, domain_name, pattern, hosts_path)
            try:
                client.api.connect_container_to_network(container_name, dnr_network_name, aliases=aliases)
                logging.info(f'[START] Container {container_name} already connected to {dnr_network_name}')
            except APIError:
                logging.warning(f'[START] Container {container_name} already connected')

        if is_die(event):
            container_name = get_container_name(event)
            pattern = build_hosts_pattern(container_name, escaped_domain_name)
            remove_from_hosts(pattern, hosts_path)
            try:
                client.api.disconnect_container_from_network(container_name, dnr_network_name)
                logging.info(f'[DIE] Container {container_name} already disconnected from {dnr_network_name}')
            except APIError:
                logging.warning(f'[DIE] Container {container_name} already disconnected from {dnr_network_name}')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'exception: {exc} trace: {traceback.format_exc()}')
