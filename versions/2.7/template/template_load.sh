#!/bin/bash

rm -f current.log create.log

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs kill -n 9

{
    echo "Removing old databases"

    mysql --connect-timeout=15 -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'DROP DATABASE IF EXISTS evaluator' 
    mysql --connect-timeout=15 -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'CREATE DATABASE evaluator'
    
    echo "STATUS: Initializing databases"
    ./bristlecone/bin/evaluator_tungsten.sh create_tables.xml
    
    echo "STATUS: Starting Bristlecone"
    ./bristlecone/bin/evaluator_tungsten.sh load_config.xml
    
    wait
} >current.log 2>&1

wait

