import os
import re

from host import build_hosts_pattern, get_hosts_paths, insert_on_hosts, remove_from_hosts


class TestHost:
    paths = ['./test1', './test2']
    fake_initial_content_1 = ''
    fake_initial_content_2 = '''
127.0.0.1	localhost
127.0.1.1	HUNB707

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
'''
    fake_initial_content_3 = '''
127.0.0.1	localhost
127.0.1.1	HUNB707

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
123.123.123.123 fake_name.dnr
'''
    fake_initial_content_4 = '''
127.0.0.1	localhost
127.0.1.1	HUNB707

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
123.123.123.123 fake_name2.dnr
123.123.123.123 fake_name.dnr
'''

    def _create_fake_file(self, content: str):
        for p in self.paths:
            with open(p, 'w') as file:
                file.write(content)

    def _delete_fake_file(self):
        for p in self.paths:
            os.remove(p)

    @staticmethod
    def test_get_hosts_paths_linux():
        paths = get_hosts_paths('linux', 'fake_release')
        expected_paths = ['/etc/hosts']
        assert paths == expected_paths

    @staticmethod
    def test_get_hosts_paths_macos():
        paths = get_hosts_paths('darwin', 'fake_release')
        expected_paths = ['/etc/hosts']
        assert paths == expected_paths

    @staticmethod
    def test_get_hosts_paths_windows():
        paths = get_hosts_paths('windows', 'fake_release')
        expected_paths = ['C:/Windows/System32/drivers/etc/hosts']
        assert paths == expected_paths

    @staticmethod
    def test_get_hosts_paths_wsl():
        paths = get_hosts_paths('linux', 'microsoft')
        expected_paths = ['/etc/hosts', 'C:/Windows/System32/drivers/etc/hosts']
        assert paths == expected_paths

    @staticmethod
    def test_build_hosts_pattern():
        expected_result = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[ \t]*fake_name\.dnr.*$')
        pattern = build_hosts_pattern('fake_name')
        assert pattern == expected_result

    @staticmethod
    def test_build_hosts_pattern_match():
        fake_string = '123.123.123.123  fake_name.dnr'
        pattern = build_hosts_pattern('fake_name')
        assert re.match(pattern, fake_string) is not None

    def test_insert_on_hosts_1(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        self._create_fake_file(self.fake_initial_content_1)
        insert_on_hosts(fake_ip, fake_name, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        expected_result = f'{fake_ip}\t{fake_name}.dnr\n'
        for c in contents:
            assert c == expected_result

    def test_insert_on_hosts_2(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        self._create_fake_file(self.fake_initial_content_2)
        insert_on_hosts(fake_ip, fake_name, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        hosts_entry = f'{fake_ip}\t{fake_name}.dnr\n'
        expected_result = self.fake_initial_content_2 + hosts_entry
        for c in contents:
            assert c == expected_result

    def test_insert_on_hosts_duplicated(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        self._create_fake_file(self.fake_initial_content_3)
        insert_on_hosts(fake_ip, fake_name, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        hosts_entry = f'{fake_ip}\t{fake_name}.dnr\n'
        expected_result = self.fake_initial_content_3
        for c in contents:
            assert c == expected_result

    def test_remove_from_hosts_3(self):
        contents = []
        pattern = build_hosts_pattern('fake_name')
        expected_result = '''
127.0.0.1	localhost
127.0.1.1	HUNB707

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
'''
        self._create_fake_file(self.fake_initial_content_3)
        remove_from_hosts(pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        for c in contents:
            assert c == expected_result

    def test_remove_from_hosts_4(self):
        contents = []
        pattern = build_hosts_pattern('fake_name2')
        expected_result = '''
127.0.0.1	localhost
127.0.1.1	HUNB707

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
123.123.123.123 fake_name.dnr
'''
        self._create_fake_file(self.fake_initial_content_4)
        remove_from_hosts(pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        for c in contents:
            assert c == expected_result
