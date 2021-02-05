# Randosoru-Server

Backend of guild.randosoru.me


## Getting Started

### Prerequisites

* MySQL Server
* [Discord OAuth2 App](https://discord.com/developers/applications)
* [Line Login App](https://developers.line.biz/en/)

### Installation

1. Install all required modules from pip. `pip3 install -r requirements.txt`
2. Rename `config.py.example` to `config.py` and modify it.


## Deployment

#### Behind a Proxy

If you are using Nginx or any proxy server, add the following rules to your config.

```conf
location /api/ {
  proxy_pass http://{SERVER_IP}/;
}

location /socket.io {
  proxy_pass http://{SERVER_IP};
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "Upgrade";
  proxy_set_header Host $host;
}
```

#### Without Docker

Run `uvicorn main:app --host 0.0.0.0 --port 80` to start a server at `0.0.0.0:80`.

#### With Docker

If your MySQL server is a docker container, you may need to add `--net mysql-network` when using `docker run`.

```
docker build . -t guild-randosoru-server

docker run \
    -e VIRTUAL_HOST=guild.randosoru.me \ # for nginx-proxy
    --restart always \
    --name guild-randosoru-server \
    -d guild-randosoru-server
```