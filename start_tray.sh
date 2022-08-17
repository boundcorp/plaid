#!/usr/bin/env bash

cd $(dirname $0)

export DISPLAY=:1

pipenv run python3 menu.py
