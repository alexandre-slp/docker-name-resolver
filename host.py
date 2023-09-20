import pathlib
import re
import shutil
import string
import tempfile


def get_hosts_paths(system: str, release: str) -> list:
    on_linux = system == 'linux'
    on_macos = system == 'darwin'
    on_windows = system == 'windows'
    on_wsl = on_linux and 'microsoft' in release
    if on_wsl:
        return ['/etc/hosts', 'C:/Windows/System32/drivers/etc/hosts']

    if on_linux:
        return ['/etc/hosts']

    if on_macos:
        return ['/etc/hosts']

    if on_windows:
        return ['C:/Windows/System32/drivers/etc/hosts']


def build_hosts_pattern(name):
    return re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[ \t]*' + name + r'\.dnr.*$')


def insert_on_hosts(ip: str, name: str, paths: list):
    hosts_entry = f'{ip}\t{name}.dnr\n'
    for path in paths:
        with open(path) as original_hosts:
            content = original_hosts.read()

        if name not in content:
            if content and content[-1] in string.ascii_letters:
                content += '\n'

            parent = pathlib.Path(path).parent
            with tempfile.NamedTemporaryFile(dir=parent) as new_hosts:
                temp = f'{content}{hosts_entry}'
                b = bytes(temp, 'utf-8')
                new_hosts.write(b)
                new_hosts.seek(0)
                shutil.copy(parent.joinpath(new_hosts.name), path)


def remove_from_hosts(pattern: re.Pattern, paths: list):
    for path in paths:
        with open(path) as hosts:
            lines = hosts.readlines()
            new_lines = lines.copy()

        for ln in lines:
            if re.match(pattern, ln):
                new_lines.remove(ln)

        parent = pathlib.Path(path).parent
        with tempfile.NamedTemporaryFile(dir=parent) as new_hosts:
            byte_lines = [bytes(ln, 'utf-8') for ln in new_lines]
            new_hosts.writelines(byte_lines)
            new_hosts.seek(0)
            shutil.copy2(parent.joinpath(new_hosts.name), path)
