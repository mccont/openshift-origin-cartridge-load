#!/bin/bash

set -e
rm -f current.log create.log

echo "Removing old databases"

mysql -h 192.168.1.70 -u app_user -psecret -P 9999 -e 'DROP DATABASE IF EXISTS evaluator'
mysql -h 192.168.1.70 -u app_user -psecret -P 9999 -e 'CREATE DATABASE evaluator'

echo "Initializing databases"
./bristlecone/bin/evaluator_tungsten.sh create_tables.xml >create.log 2>&1 

echo "Starting Bristlecone..."
./bristlecone/bin/evaluator_tungsten.sh load_config.xml >current.log 2>&1 &

wait
