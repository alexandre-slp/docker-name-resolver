#!/usr/bin/python3
import logging
import sys
import traceback

import click
import docker
from docker.errors import APIError

from event import is_start, is_die, get_container_name
from network import (
    DEFAULT_DOMAIN,
    build_container_aliases,
    build_network_name,
    get_active_containers,
    can_attach_to_bridge_network,
    container_route_name,
)
from nginx import start_nginx, update_routes


def _setup_logging(is_verbose: bool) -> None:
    logging_level = logging.INFO if is_verbose else logging.ERROR
    logging.basicConfig(
        stream=sys.stdout,
        level=logging_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@click.group()
def cli() -> None:
    """Docker Name Resolver CLI."""


def _connect_container_to_dnr_network(
    client: docker.DockerClient,
    *,
    container_name: str,
    alias_base_name: str,
    dnr_network_name: str,
    domain_name: str,
    log_prefix: str,
) -> None:
    aliases = build_container_aliases(alias_base_name, domain_name)
    try:
        client.api.connect_container_to_network(
            container_name, dnr_network_name, aliases=aliases
        )
        logging.info(
            "%s Container %s connected to %s",
            log_prefix,
            container_name,
            dnr_network_name,
        )
    except APIError:
        logging.info(
            "%s Container %s already connected to %s",
            log_prefix,
            container_name,
            dnr_network_name,
        )


def _bootstrap_connect_running_containers(
    client: docker.DockerClient, *, dnr_network_name: str, domain_name: str
) -> None:
    for container in client.api.containers(filters={"status": "running"}):
        names = container.get("Names") or []
        container_name = (names[0] if names else "").lstrip("/")
        if not container_name:
            continue

        try:
            inspect = client.api.inspect_container(container.get("Id"))
        except Exception:
            continue

        network_mode = (
            inspect.get("HostConfig", {}).get("NetworkMode") if inspect else None
        )
        if not can_attach_to_bridge_network(network_mode):
            logging.info(
                "Skipping container %s due to network_mode=%s",
                container_name,
                network_mode,
            )
            continue

        _connect_container_to_dnr_network(
            client,
            container_name=container_name,
            alias_base_name=container_route_name(
                client, container_id=container.get("Id"), fallback_name=container_name
            ),
            dnr_network_name=dnr_network_name,
            domain_name=domain_name,
            log_prefix="[BOOTSTRAP]",
        )


@cli.command()
@click.option(
    "-v",
    "--verbose",
    "is_verbose",
    is_flag=True,
    default=False,
    help="Logging verbosity",
)
def start(is_verbose: bool) -> None:
    """
    Start the DNR daemon.

    It will:
    - ensure the DNR docker network exists;
    - connect existing bridge containers to the DNR network;
    - start nginx and generate initial configuration/status page;
    - listen to docker events to keep routes in sync.
    """
    _setup_logging(is_verbose)
    logging.info("Starting DNR daemon")

    client = docker.from_env()
    domain_name = DEFAULT_DOMAIN
    dnr_network_name = build_network_name(domain_name)

    try:
        client.api.create_network(dnr_network_name, check_duplicate=True)
        logging.info("Network %s created", dnr_network_name)
    except APIError:
        logging.info("Network %s already exists", dnr_network_name)

    _bootstrap_connect_running_containers(
        client, dnr_network_name=dnr_network_name, domain_name=domain_name
    )

    # Start nginx once and build initial configuration.
    start_nginx()
    routes = get_active_containers(client, dnr_network_name, domain_name)
    update_routes(routes)

    # Listen for docker events to keep configuration in sync.
    for event in client.events(decode=True):
        if is_start(event):
            if event.get("Type") and event.get("Type") != "container":
                continue

            container_name = get_container_name(event)
            if not container_name:
                continue

            try:
                inspect = client.api.inspect_container(container_name)
            except Exception:
                inspect = None

            network_mode = (
                inspect.get("HostConfig", {}).get("NetworkMode") if inspect else None
            )
            if not can_attach_to_bridge_network(network_mode):
                logging.info(
                    "[START] Skipping container %s due to network_mode=%s",
                    container_name,
                    network_mode,
                )
                continue

            _connect_container_to_dnr_network(
                client,
                container_name=container_name,
                alias_base_name=container_route_name(
                    client,
                    container_id=event.get("id") or container_name,
                    fallback_name=container_name,
                ),
                dnr_network_name=dnr_network_name,
                domain_name=domain_name,
                log_prefix="[START]",
            )

            routes = get_active_containers(client, dnr_network_name, domain_name)
            update_routes(routes)

        if is_die(event):
            if event.get("Type") and event.get("Type") != "container":
                continue

            container_name = get_container_name(event)
            if not container_name:
                continue
            try:
                client.api.disconnect_container_from_network(
                    container_name, dnr_network_name
                )
                logging.info(
                    "[DIE] Container %s disconnected from %s",
                    container_name,
                    dnr_network_name,
                )
            except APIError:
                logging.info(
                    "[DIE] Container %s already disconnected from %s",
                    container_name,
                    dnr_network_name,
                )

            routes = get_active_containers(client, dnr_network_name, domain_name)
            update_routes(routes)


@cli.command()
def list() -> None:
    """
    List active container routes.

    This command is intended to be executed via:
    docker exec -it dnr ./dnr list
    """
    client = docker.from_env()
    domain_name = DEFAULT_DOMAIN
    dnr_network_name = build_network_name(domain_name)
    routes = get_active_containers(client, dnr_network_name, domain_name)

    if not routes:
        print("No active routes")
        return

    print("CONTAINER\tHOST\tIP\tPORT")
    for route in routes:
        port_str = "" if route.port in (80, 443) else str(route.port)
        print(f"{route.name}\t{route.host}\t{route.ip}\t{port_str}")


if __name__ == "__main__":
    try:
        cli()
    except Exception as exc:
        print(f"exception: {exc} trace: {traceback.format_exc()}")
