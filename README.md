# CUPS-docker - CUPS on a Container

Run a CUPS instance (in proxy mode or full-server mode) on a container.

Container packages are available from Docker Hub and Github Container Registry (ghcr.io)
  - Docker Hub Image: `infra7/cups`
  - GHCR Image: `ghcr.io/infra7ti/cups`

## Usage

- Quick start with default parameters (full server mode):
```bash
mkdir -p ./config/{avahi,cups}

docker run -d \
  --name cups \
  --ulimit nofile=65535:65535 \
  -p 631:631 \
  infra7/cups
```

- Customizing your container (full server mode):
```bash
mkdir -p ./config/{avahi,cups}

docker run -d \
  --name cups \
  --restart unless-stopped \
  --ulimit nofile=65535:65535 \
  --device /dev/bus/usb \
  -e TZ="America/Sao_Paulo" \
  -e CUPSADMIN=joe \
  -e CUPSPASSWORD=JoEpaS$w0rD \
  -e START_DBUS_DAEMON=ON \
  -e START_AVAHI_DAEMON=ON \
  -v ./config/cups/:/etc/cups/ \
  -v ./config/avahi/:/etc/avahi/ \
  -p 631:631 \
  infra7/cups
```
> Note: Using docker secrets (see ENV variables below) and changing the default username and password is highly recommended.

### Parameters and defaults
- `--port` -> default cups network port `631:631`. Change not recommended unless you know what you're doing
- `--ulimit` -> specify the user limits for cups process: for example, to set nofile pass `nofile=65535:65535`.

#### Optional parameters
- `--name` -> whatever you want to call your docker image. using `cups` in the example above.
- `--device` -> used to give docker access to USB printer. Default passes the whole USB bus `/dev/bus/usb`, in case you change the USB port on your device later. change to specific USB port if it will always be fixed, for eg. `/dev/bus/usb/001/005`.
- `-v|--volume` -> adds a persistent volume for CUPS config files if you need to migrate or start a new container with the same settings

Environment variables that can be changed to suit your needs, use the `-e` tag
| Parameter          | Default                    | Type    | Description                                  |
| ------------------ | -------------------------- | ------- | -------------------------------------------- |
| TZ                 | "Etc/UTC"                  | string  | Time zone of your server                     |
| CUPSADMIN          | admin                      | string  | Name of the admin user for server            |
| CUPSPASSWORD       | \_\_cUPsPassw0rd\_\_       | string  | Password for server admin                    |
| CUPSADMINFILE      | /run/secrets/cups_admin    | string  | Filename storing admin username on container |
| CUPSPASSWORDFILE   | /run/secrets/cups_password | string  | Filename storing admin password on container |
| CUPSERRORLOG       | /dev/stderr                | string  | Where to write error_log content             |
| START_DBUS_DAEMON  | OFF                        | boolean | Whether starts dbus-daemon with container    |
| START_AVAHI_DAEMON | OFF                        | boolean | Whether starts avahi-daemon with container   |

### With docker-compose
```yaml
name: printing

services:
  cupsd:
    environment:
      CUPSADMINFILE: /run/secrets/cups_admin
      CUPSPASSWORDFILE: /run/secrets/cups_password
      START_DBUS_DAEMON: ON
      START_AVAHI_DAEMON: ON
    healthcheck:
      interval: 10s
      retries: 5
      start_period: 5s
      timeout: 5s
    image: infra7/cups:latest
    ports:
      - 631:631
      - 5353:5353/udp
    restart: unless-stopped
    secrets:
      - cups_admin
      - cups_password
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - ${PWD}/config/cups/:/etc/cups/
      - ${PWD}/config/avahi/:/etc/avahi/

networks:
  default:
    name: printing

secrets:
  cups_admin:
    file: ${PWD}/secrets/cups_admin
  cups_password:
    file: ${PWD}/secrets/cups_password
```

## Server Administration
You should now be able to access CUPS admin server using the IP address of your headless computer/server 
http://192.168.xxx.xxx:631, or whatever.

If your server has avahi-daemon/mdns running you can use the hostname, ie: http://printer.local:631. 
(IP and hostname will vary, these are just examples)

If you are running this on your PC, i.e. not on a headless server, you should be able to log in on http://localhost:631

## Thanks
This project starts as a fork of the work done by:
 **RagingTiger**: [https://github.com/RagingTiger/cups-airprint](RagingTiger/cups-airprint)
 **Anujdatar**: [https://github.com/anujdatar/cups-docker](anujdatar/cups-docker)
