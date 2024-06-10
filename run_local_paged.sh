#!/bin/bash

pagesize=$1
size=$(cat input.json | jq '.domains | length')
pages=$((($size + $pagesize - 1) / $pagesize)) # Round Up
failed_count=0
for i in $(seq 0 $(($pages - 1))); do # seq is inclusive, so -1
  python main.py $i $pagesize
  code=$?
  if (($code < 0)); then
    echo "Execution #$i halted execution"
  else
    failed_count=$(($failed_count + $code))
  fi
done

echo "Paged execution completed with $failed_count invalid domains"
