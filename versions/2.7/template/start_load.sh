#!/bin/bash

rm -f current.log create.log

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs kill -9

echo "Removing old databases"

mysql -h 192.168.1.70 -u app_user -psecret -P 9999 -e 'DROP DATABASE IF EXISTS evaluator' >mysql.log 2>&1
mysql -h 192.168.1.70 -u app_user -psecret -P 9999 -e 'CREATE DATABASE evaluator' >>mysql.log 2>&1

echo "Initializing databases"
./bristlecone/bin/evaluator_tungsten.sh create_tables.xml >create.log 2>&1 

echo "Starting Bristlecone..."
./bristlecone/bin/evaluator_tungsten.sh load_config.xml >current.log 2>&1 &

wait
