#!/bin/bash

set -e
rm -f current.log create.log

echo "Removing old databases"

mysql -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'DROP DATABASE IF EXISTS evaluator'
mysql -h @@REALHOST@@ -u @@USER@@ -p@@PASSWORD@@ -P @@HOSTPORT@@ -e 'CREATE DATABASE evaluator'

echo "Initializing databases"
./bristlecone/bin/evaluator_tungsten.sh create_tables.xml >create.log 2>&1 

echo "Starting Bristlecone..."
./bristlecone/bin/evaluator_tungsten.sh load_config.xml >current.log 2>&1 &

wait
