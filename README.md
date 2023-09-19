# Docker Name Resolver (DNR)
```
    ____  _   ______  
   / __ \/ | / / __ \ 
  / / / /  |/ / /_/ / 
 / /_/ / /|  / _, _/  
/_____/_/ |_/_/ |_|   
```
It is a simple script to sync `hosts` file with container IPs listening to Docker events.

Original content example:
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

After starting the container `my_service`:
```
127.0.0.1	localhost
127.0.1.1	HOST

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.2	my_service #DNR
```

Now it is possible to ping container name and host will be able to resolve it.

When container stop the line is removed from `hosts`.

## Requirements
- docker

## Make
| target | explanation |
|-------|-----------------|
| build | Build DNR image |  
| rmi | Remove DNR image |  
| stop | Stop DNR |  
| test | Run tests |  
| unix | Run DNR on unix systems |  
| windows | Run DNR on windows system |  
| wsl | Run DNR on wsl system |  

## Spported Systems
- Unix based (Ubuntu, Mac..)
- Windows
- WSL
