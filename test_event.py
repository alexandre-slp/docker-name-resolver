from event import is_start, is_die, get_container_name, get_container_ip


class TestEvent:
    @staticmethod
    def test_is_start():
        mock_event = {'status': 'start'}
        assert is_start(mock_event) is True

    @staticmethod
    def test_is_not_start():
        mock_event = {'status': 'other'}
        assert is_start(mock_event) is False

    @staticmethod
    def test_is_die():
        mock_event = {'status': 'die'}
        assert is_die(mock_event) is True

    @staticmethod
    def test_is_not_die():
        mock_event = {'status': 'other'}
        assert is_die(mock_event) is False

    @staticmethod
    def test_get_container_name():
        mock_event = {'Actor': {'Attributes': {'name': 'fake_name'}}}
        assert get_container_name(mock_event) == 'fake_name'

    @staticmethod
    def test_get_container_ip():
        mock_event = {'id': 'fake_id'}
        mock_network = {'Containers': {'fake_id': {'IPv4Address': '123.123.123.123/16'}}}
        assert get_container_ip(mock_event, mock_network) == '123.123.123.123'
