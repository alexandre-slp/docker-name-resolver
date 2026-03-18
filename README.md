# Docker Name Resolver (DNR)
```
    ____  _   ______  
   / __ \/ | / / __ \ 
  / / / /  |/ / /_/ / 
 / /_/ / /|  / _, _/  
/_____/_/ |_/_/ |_|   
```
It's a simple way to resolve the Docker container name to its IP using an
internal nginx reverse proxy and the special `.localhost` domain.

When a container `my_service` is running, DNR will expose it as
`http://my_service.localhost` from your host machine (Linux, Mac or Windows),
without changing the host's `hosts` file or requiring a custom DNS server.

## Requirements
- Docker

## Tested Systems
- Ubuntu  
  ```
  docker run --restart unless-stopped --detach --tty \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --publish 80:80 --publish 443:443 \
    --name dnr alexandreslp/docker-name-resolver
  ```

## Supported Systems
- Linux, Mac & WSL  
  ```
  docker run --restart unless-stopped --detach --tty \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --publish 80:80 --publish 443:443 \
    --name dnr alexandreslp/docker-name-resolver
  ```
- Windows (Docker Desktop)  
  ```
  docker run --restart unless-stopped --detach --tty \
    --volume //./pipe/docker_engine:/var/run/docker.sock \
    --publish 80:80 --publish 443:443 \
    --name dnr alexandreslp/docker-name-resolver
  ```

## Architecture

```mermaid
graph TD
    UserBrowser([Browser / Curl <br> http://db.localhost]) --> ResolveLocalhost
    UserCLI([Host Terminal <br> docker exec dnr list]) -.-> DNR_CLI

    subgraph Host_OS [Host OS (Linux, Mac, Windows)]
        ResolveLocalhost[OS resolves .localhost <br> to 127.0.0.1] --> PortMap[Docker port mapping <br> Port 80]
    end

    PortMap --> NginxProxy
    
    subgraph Container_DNR [DNR Container]
        NginxProxy[Nginx Reverse Proxy]
        StatusPage[index.html status page <br> at http://localhost/]
        NginxProxy -.-> StatusPage

        subgraph Python_Process [Python Process (PID 1)]
            DNR_Daemon[Event daemon]
            TruthSource[get_active_containers()]
            NginxManager[nginx.py <br> Generates .conf and .html]
            DNR_CLI[Comando CLI: list]
        end

        DNR_Daemon -.->|Reads start/die events| TruthSource
        TruthSource -.->|Network data| NginxManager
        NginxManager -.->|Generates configs| NginxProxy
        NginxManager -.->|Generates status page| StatusPage
        DNR_CLI -.->|Queries| TruthSource
    end

    DNR_Daemon <==>|socket| DockerSock([/var/run/docker.sock])
    TruthSource <==>|inspects networks| DockerSock
    
    NginxProxy -->|proxy_pass| TargetIP([Target Container <br> ex: db IP 172.18.0.2])
```

## Usage

After starting DNR, any running container will be connected to the DNR network
and available as:

```
http://<container_name>.localhost
```

You can also see a simple HTML status page with all active routes at:

```
http://localhost
```

And you can list the routes from the CLI with:

```
docker exec -it dnr ./dnr list
```

The `list` command prints only the fields that matter in a terminal:

- `CONTAINER`: the route/container name
- `IP`: the IP address in the DNR network
- `PORTS`: one or more exposed ports, joined by ` | ` (example: `80 | 443`)

Sorting defaults to the same as the status table (container name ascending),
and can be customized:

```
# Sort by container name (ascending/descending)
docker exec -it dnr ./dnr list --sort name --order asc
docker exec -it dnr ./dnr list --sort name --order desc

# Sort by IP (ascending/descending)
docker exec -it dnr ./dnr list --sort ip --order asc
docker exec -it dnr ./dnr list --sort ip --order desc
```

## FAQ
- Problem: `Name or service not known`
    - Solution: Clear DNS cache `sudo apt-get -y install nscd && sudo service nscd restart`
