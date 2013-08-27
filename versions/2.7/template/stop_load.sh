#!/bin/bash

echo Killing any existing bristlecone processes

KILLCMD='kill -s 9'

if [ `uname` == 'Darwin' ]
then
    KILLCMD='kill -s kill'
fi

ps -ef|grep bristlecone.evaluator|grep -v grep|awk '{ print $2; }'| xargs $KILLCMD
ps -ef|grep start_load.sh|grep -v grep|awk '{ print $2; }'| xargs $KILLCMD

