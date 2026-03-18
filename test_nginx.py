from network import ContainerRoute
from nginx import render_nginx_config, render_status_page


class TestNginx:
    @staticmethod
    def test_render_nginx_config():
        routes = [
            ContainerRoute(name="svc1", ip="10.0.0.2", host="svc1.localhost", port=80),
        ]
        config = render_nginx_config(routes)

        assert "server_name svc1.localhost;" in config
        assert "proxy_pass http://10.0.0.2;" in config

    @staticmethod
    def test_render_nginx_config_non_default_port():
        routes = [
            ContainerRoute(name="echo", ip="10.0.0.4", host="echo.localhost", port=5678),
        ]
        config = render_nginx_config(routes)

        assert "proxy_pass http://10.0.0.4:5678;" in config

    @staticmethod
    def test_render_nginx_config_dnr_localhost_serves_status_page():
        routes = [
            ContainerRoute(
                name="dnr", ip="10.0.0.10", host="dnr.localhost", port=80
            ),
        ]
        config = render_nginx_config(routes)

        assert "server_name dnr.localhost;" in config
        assert "root /usr/share/nginx/html;" in config
        assert "index index.html;" in config
        assert "proxy_pass" not in config

    @staticmethod
    def test_render_status_page():
        routes = [
            ContainerRoute(name="svc1", ip="10.0.0.2", host="svc1.localhost", port=80),
            ContainerRoute(name="svc2", ip="10.0.0.3", host="svc2.localhost", port=80),
        ]
        html = render_status_page(routes)

        assert "svc1" in html
        assert "svc1.localhost" in html
        assert "10.0.0.2" in html
        assert "svc2" in html
        assert "svc2.localhost" in html
        assert "10.0.0.3" in html

