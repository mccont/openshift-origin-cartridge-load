#!/bin/bash

rm -f current.log create.log

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs kill -s KILL

{
    echo "Removing old databases"

    mysql --connect-timeout=15 -h 192.168.2.20 -u app_user -ppassword -P 9999 -e 'DROP DATABASE IF EXISTS evaluator' 
    mysql --connect-timeout=15 -h 192.168.2.20 -u app_user -ppassword -P 9999 -e 'CREATE DATABASE evaluator'
    
    echo "STATUS: Initializing databases"
    ./bristlecone/bin/evaluator_tungsten.sh create_tables.xml
    
    echo "STATUS: Starting Bristlecone"
    ./bristlecone/bin/evaluator_tungsten.sh load_config.xml
    
    wait
} >current.log 2>&1

wait

