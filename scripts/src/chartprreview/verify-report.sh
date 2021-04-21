#!/bin/bash

getAnnotations() {

  report=$1

  annotations=()

  metadata=false
  tool=false
  chart=false
  chartannotations=false


  while IFS= read -r line; do
    line=`echo $line | xargs`
    if [[ $line == "metadata:"* ]]; then
      metadata=true
    elif [[ $line == "results:"* ]]; then
      metadata=false
    elif [ "$metadata" = true ]; then
      if [[ $line == *"tool:" ]]; then
          tool=true
          chart=false
      elif [[ $line == *"chart:" ]]; then
          tool=false
          chart=true
      elif [ "$tool" = true ]; then
        if [[ $line == "digest:"* ]]; then
            digest=`echo "$line" | sed 's/digest://' | xargs`
            annotations+=("\"helm-chart.openshift.io/digest\":\"$digest\"")
        elif [[ $line == "lastCertifiedTime:"* ]]; then
            certtime=`echo "$line" | sed 's/lastCertifiedTime://' | xargs`
            annotations+=("\"helm-chart.openshift.io/lastCertifiedTime\":\"$certtime\"")
        fi
      elif [ "$chart" = true ]; then
        if [[ $line == "annotations:"* ]]; then
            chartannotations=true
        elif [ "$chartannotations" = true ]; then
          if [[ $line == "helm-chart.openshift.io/"* ]]; then
             name=`echo $line | cut -d: -f1 | xargs`
             value=`echo "$line" | sed "s#$name:##" | xargs`
             annotations+=("\"$name\":\"$value\"")
          fi
        fi
      fi
    fi

  done < $report

  output="{"
  addComma=false
  for annotation in "${annotations[@]}"; do
    if [ "$addComma" = true ]; then
      output+=", "
    fi
    output+="$annotation"
    addComma=true
  done
  output+="}"

  echo $output
}

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

  output="{\"passed\": $passed, \"failed\": ${#fails[@]}"
  if [ ${#fails[@]} -gt 0 ]; then
      output+=", \"message\": ["
      addComma=false
      for fail in "${fails[@]}"; do
        if [ "$addComma" = true ]; then
          output+=","
        fi
        output+="\"$fail\""
        addComma=true
      done
  fi
  output+="]}"
  echo $output

}

command=$1
report=$2
chart=$3

if [ -z "$report" ]; then
  echo "{\"error\": \"report must be specified\"}"
  exit
fi

if [ ! -f "$report" ]; then
  echo "{\"error\": \"report does not exist\"}"
  exit
fi


if [ $command == "results" ]; then
  getFails "$report"
elif  [ $command == "annotations" ]; then
  getAnnotations "$report"
else
  echo "{\"error\": \"$command is not a valid command\"}"
fi

