#!/bin/bash +e

rm -f current.log create.log

{
    echo "STATUS: Removing old databases"

    mysql --connect-timeout=15 -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'DROP DATABASE IF EXISTS evaluator' 

    echo "STATUS: Creating new databases"

    mysql --connect-timeout=15 -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'CREATE DATABASE evaluator'
    
    echo "STATUS: Initializing databases"
    ./bristlecone/bin/evaluator_tungsten.sh create_tables.xml
    
    while true
    do
        echo "STATUS: Starting Bristlecone"
        ./bristlecone/bin/evaluator_tungsten.sh load_config.xml
    done
    
    wait
} >current.log 2>&1

wait

