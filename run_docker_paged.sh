#!/bin/bash

docker build -t whois_scanner:latest .

if [ -z "$1" ]; then
  pagesize=100
else
  pagesize=$1
fi

size=$(cat input.json | jq '.domains | length')
pages=$((($size + $pagesize - 1) / $pagesize)) # Round Up
failed_count=0
for i in $(seq 0 $(($pages - 1))); do # seq is inclusive, so -1
  docker run -it whois_scanner:latest $i $pagesize
  code=$?
  if (($code < 0)); then
    echo "Execution #$i halted execution"
  else
    failed_count=$(($failed_count + $code))
  fi
done

echo "Paged execution completed with $failed_count invalid domains"
