from network import (
    DEFAULT_DOMAIN,
    ContainerRoute,
    build_container_aliases,
    build_network_name,
    get_active_containers,
    can_attach_to_bridge_network,
)


class FakeApi:
    def __init__(self, network_data, container_ports=None, container_labels=None):
        self._network_data = network_data
        self._container_ports = container_ports or {}
        self._container_labels = container_labels or {}

    def inspect_network(self, _name):
        return self._network_data

    def inspect_container(self, container_id):
        ports = self._container_ports.get(container_id, {"80/tcp": {}})
        labels = self._container_labels.get(container_id, {})
        return {"Config": {"ExposedPorts": ports, "Labels": labels}}


class FakeClient:
    def __init__(self, network_data, container_ports=None, container_labels=None):
        self.api = FakeApi(network_data, container_ports, container_labels)


class TestNetwork:
    @staticmethod
    def test_build_network_name():
        expected_result = "localhost-network"
        result = build_network_name(".localhost")
        assert result == expected_result

    @staticmethod
    def test_build_network_name_fail():
        expected_result = Exception('Malformed domain name. Good domain name example: ".localhost"')
        try:
            build_network_name("localhost")
        except Exception as exc:
            assert exc.args == expected_result.args

    @staticmethod
    def test_build_container_aliases_default_domain():
        expected_result = ["fake_name", "fake_name.localhost"]
        result = build_container_aliases("fake_name", DEFAULT_DOMAIN)
        assert result == expected_result

    @staticmethod
    def test_build_container_aliases_normalizes_name():
        expected_result = ["fake_name", "fake_name.localhost"]
        result = build_container_aliases("/fake_name", DEFAULT_DOMAIN)
        assert result == expected_result

    @staticmethod
    def test_is_unconnectable_network_mode():
        assert can_attach_to_bridge_network("host") is False
        assert can_attach_to_bridge_network("none") is False
        assert can_attach_to_bridge_network("bridge") is True
        assert can_attach_to_bridge_network(None) is True

    @staticmethod
    def test_get_active_containers():
        network_data = {
            "Containers": {
                "id1": {
                    "Name": "svc1",
                    "IPv4Address": "10.0.0.2/24",
                },
                "id2": {
                    "Name": "svc2",
                    "IPv4Address": "10.0.0.3/24",
                },
            }
        }
        client = FakeClient(network_data)
        routes = get_active_containers(client, "localhost-network", DEFAULT_DOMAIN)

        assert routes == [
            ContainerRoute(name="svc1", ip="10.0.0.2", host="svc1.localhost", ports=[80]),
            ContainerRoute(name="svc2", ip="10.0.0.3", host="svc2.localhost", ports=[80]),
        ]

    @staticmethod
    def test_get_active_containers_compose_service_name():
        network_data = {
            "Containers": {
                "id1": {
                    "Name": "docker-name-resolver-echo2-1",
                    "IPv4Address": "10.0.0.10/24",
                }
            }
        }
        labels = {"id1": {"com.docker.compose.service": "echo2"}}
        client = FakeClient(network_data, container_labels=labels)
        routes = get_active_containers(client, "localhost-network", DEFAULT_DOMAIN)

        assert routes == [
            ContainerRoute(name="echo2", ip="10.0.0.10", host="echo2.localhost", ports=[80]),
        ]

