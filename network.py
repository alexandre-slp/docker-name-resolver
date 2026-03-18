import re
from dataclasses import dataclass
import ipaddress
from typing import Dict, List, Literal, Optional

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
    normalized_name = name.lstrip("/")
    return [normalized_name, f"{normalized_name}{domain}"]


def container_route_name(
    client: docker.DockerClient, *, container_id: str, fallback_name: str
) -> str:
    """
    Determine the name used for routing and status.

    If the container was created by Docker Compose, prefer the service name
    (e.g., "echo2") over the generated container name
    (e.g., "project-echo2-1").
    """
    normalized_fallback = fallback_name.lstrip("/")
    try:
        inspect = client.api.inspect_container(container_id)
    except Exception:
        return normalized_fallback

    labels: Dict[str, str] = inspect.get("Config", {}).get("Labels") or {}
    compose_service = labels.get("com.docker.compose.service")
    return (compose_service or normalized_fallback).lstrip("/")


def can_attach_to_bridge_network(network_mode: Optional[str]) -> bool:
    """
    Return True if the container can be attached to an additional
    user-defined bridge network.
    """
    return network_mode not in ("host", "none")


@dataclass
class ContainerRoute:
    name: str
    ip: str
    host: str
    ports: List[int]


def _parse_exposed_ports(exposed: Dict) -> List[int]:
    ports: List[int] = []
    for key in exposed:
        port_token = key.split("/")[0] if "/" in key else key
        try:
            ports.append(int(port_token))
        except ValueError:
            continue

    return sorted(set(ports))


def primary_port(ports: List[int]) -> int:
    """
    Prefer 80, then 443, then the first port; default to 80.
    """
    if not ports:
        return 80
    if 80 in ports:
        return 80
    if 443 in ports:
        return 443
    return ports[0]


def format_ports_for_display(ports: List[int]) -> str:
    """
    Display ports as a single string separated by ' | '.
    """
    normalized = sorted(set(ports))
    return " | ".join(str(p) for p in normalized)


SortBy = Literal["name", "ip"]
SortOrder = Literal["asc", "desc"]


def sort_routes(
    routes: List[ContainerRoute],
    *,
    sort_by: SortBy = "name",
    order: SortOrder = "asc",
) -> List[ContainerRoute]:
    """
    Sort routes for display.

    Defaults match the status table: name ascending.
    """

    def key_name(route: ContainerRoute) -> str:
        return route.name

    def key_ip(route: ContainerRoute) -> int:
        try:
            return int(ipaddress.ip_address(route.ip))
        except Exception:
            return 0

    key_fn = key_name if sort_by == "name" else key_ip
    reverse = order == "desc"
    return sorted(routes, key=key_fn, reverse=reverse)


def _container_ports(client: docker.DockerClient, container_id: str) -> List[int]:
    """
    Collect exposed ports; default to [80] when unknown/none.
    """
    try:
        inspect = client.api.inspect_container(container_id)
        exposed = inspect.get("Config", {}).get("ExposedPorts") or {}
    except Exception:
        return [80]

    ports = _parse_exposed_ports(exposed)
    return ports or [80]


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
        fallback_name = container_info.get("Name") or ""
        if not fallback_name:
            continue

        name = container_route_name(
            client, container_id=container_id, fallback_name=fallback_name
        )
        host = f"{name}{domain}"
        ports = _container_ports(client, container_id)
        routes.append(ContainerRoute(name=name, ip=ip, host=host, ports=ports))

    return routes

