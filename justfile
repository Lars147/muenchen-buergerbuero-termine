# in order to use it you need to install https://just.systems/

default:
    @just --list

[no-cd]
frontend:
    python -m http.server -d ./docs

[no-cd]
server:
    python webpush/server.py

up *args:
    docker compose -f webpush/docker-compose.yml up {{args}}

install:
    pip install -r requirements.txt
