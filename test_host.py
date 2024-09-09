import os
import re
import stat

from host import build_hosts_pattern, build_network_name, build_container_aliases, insert_on_hosts, remove_from_hosts


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
123.123.123.123 fake_name.xpto
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
123.123.123.123\tfake_name.dnr
'''
    fake_initial_content_5 = '''
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
    def test_build_network_name():
        expected_result = 'dnr-network'
        result = build_network_name('.dnr')
        assert result == expected_result

    @staticmethod
    def test_build_network_name_fail():
        expected_result = Exception('Malformed domain name. Good domain name example: ".dnr"')
        try:
            build_network_name('dnr')
        except Exception as exc:
            assert exc.args == expected_result.args

    @staticmethod
    def test_build_hosts_pattern():
        expected_result = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[ \t]*fake_name\.dnr.*')
        pattern = build_hosts_pattern('fake_name', r'\.dnr')
        assert pattern == expected_result

    @staticmethod
    def test_build_container_aliases():
        expected_result = ['fake_name.dnr']
        result = build_container_aliases('fake_name', '.dnr')
        assert result == expected_result

    @staticmethod
    def test_build_hosts_pattern_match():
        fake_string = '123.123.123.123  fake_name.dnr'
        pattern = build_hosts_pattern('fake_name', r'\.dnr')
        assert re.match(pattern, fake_string) is not None

    def test_insert_on_hosts_1(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        fake_domain = '.dnr'
        fake_pattern = build_hosts_pattern(fake_name, re.escape(fake_domain))
        self._create_fake_file(self.fake_initial_content_1)
        insert_on_hosts(fake_ip, fake_name, fake_domain, fake_pattern, self.paths)
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
        fake_domain = '.dnr'
        fake_pattern = build_hosts_pattern(fake_name, re.escape(fake_domain))
        self._create_fake_file(self.fake_initial_content_2)
        insert_on_hosts(fake_ip, fake_name, fake_domain, fake_pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        hosts_entry = f'{fake_ip}\t{fake_name}.dnr\n'
        expected_result = self.fake_initial_content_2 + hosts_entry
        for c in contents:
            assert c == expected_result

    def test_insert_on_hosts_3(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        fake_domain = '.dnr'
        fake_pattern = build_hosts_pattern(fake_name, re.escape(fake_domain))
        self._create_fake_file(self.fake_initial_content_3)
        insert_on_hosts(fake_ip, fake_name, fake_domain, fake_pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        hosts_entry = f'{fake_ip}\t{fake_name}.dnr\n'
        expected_result = self.fake_initial_content_3 + hosts_entry
        for c in contents:
            assert c == expected_result

    def test_insert_on_hosts_duplicated(self):
        contents = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        fake_domain = '.dnr'
        fake_pattern = build_hosts_pattern(fake_name, re.escape(fake_domain))
        self._create_fake_file(self.fake_initial_content_4)
        insert_on_hosts(fake_ip, fake_name, fake_domain, fake_pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        expected_result = self.fake_initial_content_4
        for c in contents:
            assert c == expected_result

    def test_insert_on_hosts_preserve_permissions(self):
        sts = []
        fake_ip = '123.123.123.123'
        fake_name = 'fake_name'
        fake_domain = '.dnr'
        fake_pattern = build_hosts_pattern(fake_name, re.escape(fake_domain))
        self._create_fake_file(self.fake_initial_content_1)
        insert_on_hosts(fake_ip, fake_name, fake_domain, fake_pattern, self.paths)
        for p in self.paths:
            sts.append(os.stat(p))

        self._delete_fake_file()
        expected_result = int('644', base=8)
        for s in sts:
            assert stat.S_IMODE(s.st_mode) == expected_result

    def test_remove_from_hosts_3(self):
        contents = []
        pattern = build_hosts_pattern('fake_name', r'\.dnr')
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
        self._create_fake_file(self.fake_initial_content_4)
        remove_from_hosts(pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        for c in contents:
            assert c == expected_result

    def test_remove_from_hosts_4(self):
        contents = []
        pattern = build_hosts_pattern('fake_name2', r'\.dnr')
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
        self._create_fake_file(self.fake_initial_content_5)
        remove_from_hosts(pattern, self.paths)
        for p in self.paths:
            with open(p) as file:
                contents.append(file.read())

        self._delete_fake_file()
        for c in contents:
            assert c == expected_result

    def test_remove_from_hosts_preserve_permissions(self):
        sts = []
        pattern = build_hosts_pattern('fake_name2', r'\.dnr')
        self._create_fake_file(self.fake_initial_content_5)
        remove_from_hosts(pattern, self.paths)
        for p in self.paths:
            sts.append(os.stat(p))

        self._delete_fake_file()
        expected_result = int('644', base=8)
        for s in sts:
            assert stat.S_IMODE(s.st_mode) == expected_result
