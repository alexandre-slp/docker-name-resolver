import platform

import docker

from event import is_start, is_die, get_container_name, get_container_ip
from host import get_hosts_paths, insert_on_hosts, remove_from_hosts

if __name__ == '__main__':
    client = docker.from_env()
    system = platform.uname().system.lower()
    release = platform.uname().release.lower()
    hosts_path = get_hosts_paths(system, release)
    for event in client.events(decode=True):
        if is_start(event):
            network = client.api.inspect_network('bridge')
            container_ip = get_container_ip(event, network)
            container_name = get_container_name(event)
            insert_on_hosts(container_ip, container_name, hosts_path)

        if is_die(event):
            container_name = get_container_name(event)
            remove_from_hosts(container_name, hosts_path)