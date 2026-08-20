# syntax=docker/dockerfile:1.7
FROM python:3.13-slim-bookworm

WORKDIR /opt/personal-cli

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra dev

COPY docker/keyringrc.cfg /root/.config/python_keyring/keyringrc.cfg
COPY docker/entrypoint.sh /usr/local/bin/personal-cli-docker
RUN chmod 0755 /usr/local/bin/personal-cli-docker

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/personal-cli-docker"]
