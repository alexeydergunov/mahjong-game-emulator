#!/bin/bash

for ((i = 0; i < 1000; i++));
do
  echo $i
  python3 main.py 2>> _infinite_log.txt
done
