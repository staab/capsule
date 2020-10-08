#!/bin/bash

export $(cat .env | xargs) && find . | entr -r ./start.sh
