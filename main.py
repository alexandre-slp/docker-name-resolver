#!/usr/bin/python3
import platform
import re

import docker
from docker.errors import APIError

from event import is_start, is_die, get_container_name, get_container_ip
from host import build_hosts_pattern, get_hosts_paths, insert_on_hosts, remove_from_hosts

if __name__ == '__main__':
    client = docker.from_env()
    system = platform.uname().system.lower()
    release = platform.uname().release.lower()
    hosts_path = get_hosts_paths(system, release)
    network_bridge = client.api.inspect_network('bridge')
    dnr_network_name = 'dnr-network'

    try:
        client.api.create_network(dnr_network_name, check_duplicate=True)
    except APIError:
        pass  # Network already exists

    pattern = re.compile(r'^.*\.dnr.*$')
    remove_from_hosts(pattern, hosts_path)
    for container_info in network_bridge.get('Containers').values():
        container_ip = container_info.get('IPv4Address').split('/')[0]
        container_name = container_info.get('Name')
        insert_on_hosts(container_ip, container_name, hosts_path)
        try:
            client.api.connect_container_to_network(container_name, dnr_network_name, aliases=[f'{container_name}.dnr'])
        except APIError:
            pass

    for event in client.events(decode=True):
        if is_start(event):
            network_bridge = client.api.inspect_network('bridge')
            container_ip = get_container_ip(event, network_bridge)
            container_name = get_container_name(event)
            insert_on_hosts(container_ip, container_name, hosts_path)
            try:
                client.api.connect_container_to_network(container_name, dnr_network_name, aliases=[f'{container_name}.dnr'])
            except APIError:
                pass

        if is_die(event):
            container_name = get_container_name(event)
            pattern = build_hosts_pattern(container_name)
            remove_from_hosts(pattern, hosts_path)
