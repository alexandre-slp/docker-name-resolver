
def is_start(event: dict) -> bool:
    return event.get('status') == 'start'


def is_die(event: dict) -> bool:
    return event.get('status') == 'die'


def get_container_name(event: dict) -> str:
    return event.get('Actor').get('Attributes').get('name')


def get_container_ip(event: dict, network: dict) -> str:
    container_id = event.get('id')
    container_info = network.get('Containers').get(container_id)
    return container_info.get('IPv4Address').split('/')[0]
