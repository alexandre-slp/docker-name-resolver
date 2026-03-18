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

    # Connect current bridge containers to the DNR network.
    network_bridge = client.api.inspect_network("bridge")
    for container_info in (network_bridge.get("Containers") or {}).values():
        container_name = container_info.get("Name")
        if not container_name:
            continue

        aliases = build_container_aliases(container_name, domain_name)
        try:
            client.api.connect_container_to_network(
                container_name, dnr_network_name, aliases=aliases
            )
            logging.info(
                "Container %s connected to %s", container_name, dnr_network_name
            )
        except APIError:
            logging.info(
                "Container %s already connected to %s",
                container_name,
                dnr_network_name,
            )

    # Start nginx once and build initial configuration.
    start_nginx()
    routes = get_active_containers(client, dnr_network_name, domain_name)
    update_routes(routes)

    # Listen for docker events to keep configuration in sync.
    for event in client.events(decode=True):
        if is_start(event):
            container_name = get_container_name(event)
            aliases = build_container_aliases(container_name, domain_name)
            try:
                client.api.connect_container_to_network(
                    container_name, dnr_network_name, aliases=aliases
                )
                logging.info(
                    "[START] Container %s connected to %s",
                    container_name,
                    dnr_network_name,
                )
            except APIError:
                logging.info(
                    "[START] Container %s already connected to %s",
                    container_name,
                    dnr_network_name,
                )

            routes = get_active_containers(client, dnr_network_name, domain_name)
            update_routes(routes)

        if is_die(event):
            container_name = get_container_name(event)
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

    print("CONTAINER\tHOST\tPORT\tIP")
    for route in routes:
        port_str = "" if route.port in (80, 443) else str(route.port)
        print(f"{route.name}\t{route.host}\t{port_str}\t{route.ip}")


if __name__ == "__main__":
    try:
        cli()
    except Exception as exc:
        print(f"exception: {exc} trace: {traceback.format_exc()}")
