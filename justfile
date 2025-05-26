# Guidelines for new commands
# - Start with a verb
# - Keep it short (max. 3 words in a command)
# - Group commands by context. Include group name in the command name.
# - Mark things private that are util functions with [private] or _var
# - Don't over-engineer, keep it simple.
# - Don't break existing commands
# - Run just --fmt --unstable after adding new commands

set dotenv-load := true

# ---------------------------------------------------------------------------------------------------------------------
# Private vars

_red := '\033[1;31m'
_cyan := '\033[1;36m'
_green := '\033[1;32m'
_yellow := '\033[1;33m'
_nc := '\033[0m'

# ---------------------------------------------------------------------------------------------------------------------
# Aliases

alias rj := run-jupyter
alias rs := run-server

# ---------------------------------------------------------------------------------------------------------------------

@default:
    just --list

[group('utils')]
run-jupyter jupyter_args="":
    # uv sync

    uv run --frozen --with "jupyterlab" \
        jupyter lab {{ jupyter_args }}


# ---------------------------------------------------------------------------------------------------------------------


[group('server')]
run-server config_path="":
    #!/bin/bash
    set -euo pipefail

    # if the config_path is not empty string,set syftbox client config path
    if [ "{{config_path}}" != "" ]; then
        echo "${_green}Using custom config path: ${config_path}${_nc}"
        export SYFTBOX_CLIENT_CONFIG_PATH="${config_path}"
    fi
    
    uv run  \
        uvicorn server.main:app --reload

# ---------------------------------------------------------------------------------------------------------------------

# Build syftbox enclave wheel
[group('build')]
build:
    rm -rf dist
    uv build .

# ---------------------------------------------------------------------------------------------------------------------

# Publish Syftbox wheel to pypi
[group('publish')]
publish-pypi: (build)
    #!/bin/bash
    echo "{{ _cyan }}Publishing to pypi...{{ _nc }}"
    uvx twine upload ./dist/*
    echo "{{ _green }}Done!{{ _nc }}"