#!/bin/bash

rm -rf .venv
uv venv -p 3.12
uv pip install -r app/requirements.txt
uv run app/main.py