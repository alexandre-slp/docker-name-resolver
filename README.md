# Docker Name Resolver (DNR)
```
    ____  _   ______  
   / __ \/ | / / __ \ 
  / / / /  |/ / /_/ / 
 / /_/ / /|  / _, _/  
/_____/_/ |_/_/ |_|   
```
It's a simple way to resolve the Docker container name to it's IP.

`hosts` original content example:
```
127.0.0.1	localhost
127.0.1.1	HOST

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2	ip6-allrouters
```

After the start of `my_service` container:
```
127.0.0.1	localhost
127.0.1.1	HOST

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.2	my_service.dnr
```

Now it's possible to ping container name and host will be able to resolve it.

When container stops the line is removed from `hosts`.

## Requirements
- Docker

## Tested Systems
- Ubuntu  
  ```
  docker run --restart unless-stopped --detach --tty --volume /var/run/docker.sock:/var/run/docker.sock --volume /etc/hosts:/dnr/hosts --name dnr alexandreslp/docker-name-resolver [options]
  ```

## Not Working on =(
- Mac & WSL  
  ```
  docker run --restart unless-stopped --detach --tty --volume /var/run/docker.sock:/var/run/docker.sock --volume /etc/hosts:/dnr/hosts --name dnr alexandreslp/docker-name-resolver [options]
  ```
- Windows  
  ```
  docker run --restart unless-stopped --detach --tty --volume //./pipe/docker_engine:/var/run/docker.sock --volume C:/Windows/System32/drivers/etc/hosts:/dnr/hosts --name dnr alexandreslp/docker-name-resolver [options]
  ```

## Options
- `-d name | --domain_name name` Ex.: `-d .dnr`
  Command ex.:
  ```
  docker run --restart unless-stopped --detach --tty --volume /var/run/docker.sock:/var/run/docker.sock --volume /etc/hosts:/dnr/hosts --name dnr alexandreslp/docker-name-resolver --domain_name .xpto
  ```
## FAQ
- Problem: `Name or service not known`
    - Solution: Clear DNS cache `sudo apt-get -y install nscd && sudo service nscd restart`
