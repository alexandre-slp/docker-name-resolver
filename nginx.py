import subprocess
from pathlib import Path
from typing import Iterable

from network import ContainerRoute, format_ports_for_display, primary_port

NGINX_CONF_DIR = Path("/etc/nginx/conf.d")
NGINX_STATUS_PAGE = Path("/usr/share/nginx/html/index.html")
STATUS_TEMPLATE = Path("/dnr/status_template.html")


def render_nginx_config(routes: Iterable[ContainerRoute]) -> str:
    servers = []
    for route in routes:
        if route.host == "dnr.localhost":
            server_block = """
server {
    listen 8080;
    server_name dnr.localhost;

    root /usr/share/nginx/html;
    index index.html;
}
"""
        else:
            port = primary_port(route.ports)
            upstream = (
                f"http://{route.ip}:{port}"
                if port != 80
                else f"http://{route.ip}"
            )
            server_block = f"""
server {{
    listen 8080;
    server_name {route.host};

    location / {{
        proxy_pass {upstream};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        servers.append(server_block.strip("\n"))

    return "\n\n".join(servers) + "\n"

def render_status_page(routes: Iterable[ContainerRoute]) -> str:
    rows = []
    for route in routes:
        port_cell = format_ports_for_display(route.ports)
        rows.append(
            f"<tr>"
            f"<td>{route.name}</td>"
            f"<td><a href=\"http://{route.host}\">{route.host}</a></td>"
            f"<td>{route.ip}</td>"
            f"<td>{port_cell}</td>"
            f"</tr>"
        )

    table_rows = "\n".join(rows)
    template_html = STATUS_TEMPLATE.read_text(encoding="utf-8")
    return template_html.replace("{{table_rows}}", table_rows)


def write_nginx_config(config: str) -> None:
    NGINX_CONF_DIR.mkdir(parents=True, exist_ok=True)
    config_path = NGINX_CONF_DIR / "dnr.conf"
    config_path.write_text(config, encoding="utf-8")


def write_status_page(html: str) -> None:
    NGINX_STATUS_PAGE.parent.mkdir(parents=True, exist_ok=True)
    NGINX_STATUS_PAGE.write_text(html, encoding="utf-8")


def start_nginx() -> None:
    """
    Start nginx process.

    This function is meant to be called once at startup. It assumes the
    container image already has nginx installed and a valid base config
    that loads files from /etc/nginx/conf.d.
    """
    # Use check=True to fail fast if nginx cannot start.
    subprocess.run(["nginx"], check=True)


def reload_nginx() -> None:
    subprocess.run(["nginx", "-s", "reload"], check=True)


def update_routes(routes: Iterable[ContainerRoute]) -> None:
    """
    Update nginx configuration and status page, then reload nginx.
    """
    routes_list = list(routes)
    config = render_nginx_config(routes_list)
    write_nginx_config(config)

    status_page = render_status_page(routes_list)
    write_status_page(status_page)

    # If nginx is not yet running, this will fail, so callers should ensure
    # start_nginx() has been called once during startup.
    reload_nginx()
