import re
from dataclasses import dataclass
from typing import List

import docker


DEFAULT_DOMAIN = ".localhost"


def build_network_name(domain: str = DEFAULT_DOMAIN) -> str:
    """
    Build the docker network name based on the domain.

    The domain must start with a dot and contain only lowercase letters and
    dots, ending with a letter. Example of a valid domain: ".localhost".
    """
    if not re.fullmatch(re.compile(r"^\.[a-z.]*[a-z]$"), domain):
        raise Exception('Malformed domain name. Good domain name example: ".localhost"')

    return f"{domain[1:]}-network"


def build_container_aliases(name: str, domain: str = DEFAULT_DOMAIN) -> list:
    return [f"{name}{domain}"]


@dataclass
class ContainerRoute:
    name: str
    ip: str
    host: str
    port: int


def _container_port(client: docker.DockerClient, container_id: str) -> int:
    """
    Prefer exposed port 80, then 443, then first exposed; default 80.
    """
    try:
        inspect = client.api.inspect_container(container_id)
        exposed = inspect.get("Config", {}).get("ExposedPorts") or {}
    except Exception:
        return 80

    ports: List[int] = []
    for key in exposed:
        if "/" in key:
            port_str = key.split("/")[0]
            try:
                ports.append(int(port_str))
            except ValueError:
                continue
        else:
            try:
                ports.append(int(key))
            except ValueError:
                continue

    if not ports:
        return 80
    if 80 in ports:
        return 80
    if 443 in ports:
        return 443
    return ports[0]


def get_active_containers(
    client: docker.DockerClient, network_name: str, domain: str = DEFAULT_DOMAIN
) -> List[ContainerRoute]:
    """
    Inspect the DNR docker network and return the active container routes.

    The returned list is the single source of truth for:
    - Nginx configuration generation
    - CLI listing of active routes
    """
    network = client.api.inspect_network(network_name)
    containers = network.get("Containers") or {}

    routes: List[ContainerRoute] = []
    for container_id, container_info in containers.items():
        ip_with_mask = container_info.get("IPv4Address") or ""
        if not ip_with_mask:
            continue

        ip = ip_with_mask.split("/")[0]
        name = container_info.get("Name") or ""
        if not name:
            continue

        host = f"{name}{domain}"
        port = _container_port(client, container_id)
        routes.append(ContainerRoute(name=name, ip=ip, host=host, port=port))

    return routes

