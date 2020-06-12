# Randosoru-Server

Backend for guild.randosoru.me

## Getting Started

### Installing

At first, install needed module with pip
```
pip install -r requirements.txt
```

Then run the command below
```
uvicorn main:app
```

It will start running at `127.0.0.1:8000`


### Deployment

This application need to run behind nginx reverse proxy
```
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr; 
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; 
}
```
