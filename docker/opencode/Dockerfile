FROM hexpm/elixir:1.20.2-erlang-29.0.4-debian-trixie-20260713-slim

ARG OPENCODE_VERSION=1.18.0

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    MIX_HOME=/opt/mix \
    HEX_HOME=/opt/hex

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        jq \
        lsof \
        pkg-config \
        procps \
        python3 \
        ripgrep \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL \
        "https://github.com/anomalyco/opencode/releases/download/v${OPENCODE_VERSION}/opencode-linux-arm64.tar.gz" \
        -o /tmp/opencode.tar.gz \
    && tar -xzf /tmp/opencode.tar.gz -C /usr/local/bin \
    && rm /tmp/opencode.tar.gz \
    && opencode --version

RUN mix local.hex --force && mix local.rebar --force

WORKDIR /workspace
