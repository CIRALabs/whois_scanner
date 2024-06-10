#!/bin/bash

pagesize=$1
size=$(cat input.json | jq '.domains | length')
pages=$((($size + $pagesize - 1) / $pagesize)) # Round Up
for i in $(seq 0 $(($pages - 1))); do # seq is inclusive, so -1
  python main.py $i $pagesize
done
