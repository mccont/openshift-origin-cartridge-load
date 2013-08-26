#!/bin/bash

echo Killing any existing bristlecone processes

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs kill -s 9
ps -ef|grep start_load.sh|grep -v grep|awk '{ print $2; }'| xargs kill -s 9

