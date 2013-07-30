#!/bin/bash

rm -f current.log create.log

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs kill -s 9

echo "Removing old databases"

mysql -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'DROP DATABASE IF EXISTS evaluator' >mysql.log 2>&1
mysql -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'CREATE DATABASE evaluator' >>mysql.log 2>&1

echo "Initializing databases"
./bristlecone/bin/evaluator_tungsten.sh create_tables.xml >create.log 2>&1 

echo "Starting Bristlecone..."
./bristlecone/bin/evaluator_tungsten.sh load_config.xml >current.log 2>&1 &

wait
