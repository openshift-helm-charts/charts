#!/bin/bash


getFails () {

  report=$1

  results=false
  fails=()
  passed=0

  while IFS= read -r line; do

    if [[ ! -z $line ]]; then
      if [[ $line == "results:"* ]]; then
        results=true
      elif [ "$results" = true ]; then
        if [[ $line == *" - "* ]]; then
            multireason=false
            check=""
            type=""
            outcome=""
            reason=""
        fi
        if [[ $line == *"check:"* ]]; then
           check=`echo $line | cut -d: -f2 | xargs`
        elif [[ $line == *"type:"* ]]; then
           type=`echo $line | cut -d: -f2 | xargs`
        elif [[ $line == *"outcome:"* ]]; then
           outcome=`echo $line | cut -d: -f2 | xargs`
        elif [[ $line == *"reason:"* ]]; then
           reason=`echo $line | cut -d: -f2 | xargs`
           if [[ $reason == *'-' ]]; then
             multireason=true
             reason=""
           fi
        elif [ "$multireason" = true ]; then
           reason=`echo $line | xargs`
        fi

        if [ -n "$check" ] && [ -n "$type" ] && [ -n "$outcome" ] && [ -n "$reason" ]; then
          if [[ $outcome != "PASS" ]] && [[ $type == "Mandatory" ]]; then
              fails+=("$reason")
          else
            passed=$((passed+1))
          fi
        fi
      fi
    fi
  done < $report

  output="{passed: $passed, failed: ${#fails[@]}"
  if [ ${#fails[@]} -gt 0 ]; then
      output+=", message: "
      for fail in "${fails[@]}"; do
        output+="$fail # "
      done
  fi
  output+="}"
  echo $output

}

command=$1
report=$2
chart=$3

if [ -z "$report" ]; then
  echo "{error: report must be specified}"
  exit
fi

if [ ! -f "$report" ]; then
  echo "{error: report does not exist}"
  exit
fi


if [ $command == "results" ]; then
  getFails "$report"
else
  echo "{error: $command is not a valid command}"
fi

