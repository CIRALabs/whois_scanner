#!/bin/bash

EXIT_CODES_FILE=/tmp/whois_scanner_exit_codes.tmp

if [ -z "$1" ]; then
  pagesize=100
else
  pagesize=$1
fi

size=$(cat input.json | jq '.domains | length')
pages=$((($size + $pagesize - 1) / $pagesize)) # Round Up
threads=$pages

# Note: Can't use the constant variable at the top for file name because the command runs in a separate bash shell
rm $EXIT_CODES_FILE 2> /dev/null
seq 0 $(($pages - 1)) | xargs -n 1 -P $threads bash -c 'python main.py $2 $1 > /tmp/whois_scanner_results_$2.json; echo $? >> /tmp/whois_scanner_exit_codes.tmp' -- $pagesize

echo
failed_count=0
i=1
for code in `cat $EXIT_CODES_FILE`; do
  if (($code < 0)); then
    echo "SUMMARY: Execution #$i halted execution"
  else
    failed_count=$(($failed_count + $code))
  fi
  ((i++))
done

echo "SUMMARY: Parallel execution completed with $failed_count invalid domains"

rm $EXIT_CODES_FILE
