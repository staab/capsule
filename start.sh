#!/bin/bash

export $(cat .env | xargs) && gunicorn --bind 0.0.0.0:$PORT app:app
