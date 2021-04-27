#!/bin/bash

mandatoryChecks=( "contains-test"
            "contains-values"
            "contains-values-schema"
            "has-minkubeversion"
            "has-readme"
            "helm-lint"
            "images-are-certified"
            "is-helm-v3"
            "not-contain-csi-objects"
            "not-contains-crds" )


getDigest() {

  report=$1

  metadata=false
  tool=false

  digestValue="Not Found"

  while IFS= read -r line; do
    line=`echo $line | xargs`
    if [[ $line == "metadata:"* ]]; then
      metadata=true
    elif [[ $line == "results:"* ]]; then
      metadata=false
    elif [ "$metadata" = true ]; then
      if [[ $line == *"tool:" ]]; then
          tool=true
      elif [[ $line == *"chart:" ]]; then
          tool=false
      elif [ "$tool" = true ]; then
        if [[ $line == "digest:"* ]]; then
          name=`echo $line | cut -d: -f1 | xargs`
          digestValue=`echo "$line" | sed "s#$name:##" | xargs`
          break;
        fi
      fi
    fi

  done < $report

  echo "$digestValue"

}

checkDigest() {

    sha1=$(getDigest "$1")

    chart=$2

    tempReport="tempReport.yaml"

    docker run -v $(pwd):/charts --rm quay.io/redhat-certification/chart-verifier:latest verify -e has-readme /charts/$chart 2> $tempReport

    sha2=$(getDigest "$tempReport")

    rm $tempReport

    if [ "$sha1" == "$sha2" ]; then
      echo "{\"result\": \"pass\" , \"message\": \"digests match\"}"
    else
      echo "{\"result\": \"fail\" , \"message\": \"digests do not match\"}"
    fi
}


getMetadata() {

  report=$1

  metadatas=()

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
        if [[ $line == "chart-uri:"* ]]; then
          name=`echo $line | cut -d: -f1 | xargs`
          value=`echo "$line" | sed "s#$name:##" | xargs`
          metadatas+=("\"$name\":\"$value\"")
        fi
      elif [ "$chart" = true ]; then
        if [[ $line == "name:"* ]]; then
             name=`echo $line | cut -d: -f1 | xargs`
             value=`echo "$line" | sed "s#$name:##" | xargs`
             metadatas+=("\"$name\":\"$value\"")
        elif [[ $line == "version:"* ]]; then
             name=`echo $line | cut -d: -f1 | xargs`
             value=`echo "$line" | sed "s#$name:##" | xargs`
             metadatas+=("\"$name\":\"$value\"")
        fi
      fi
    fi

  done < $report

  output="{"
  addComma=false
  for data in "${metadatas[@]}"; do
    if [ "$addComma" = true ]; then
      output+=", "
    fi
    output+="$data"
    addComma=true
  done
  output+="}"

  echo $output
}

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

getFails() {

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
          if [[ $line == *"Image is Red Hat certified"* ]]; then
            outcome="PASS"
          else
            outcome="FAIL"
          fi
        fi

        if [ -n "$check" ] && [ -n "$type" ] && [ -n "$outcome" ] && [ -n "$reason" ]; then
          if [[ $outcome != "PASS" ]] && [[ $type == "Mandatory" ]]; then
              fails+=("$reason")
          else
            passed=$((passed+1))
          fi
          mandatoryChecks=("${mandatoryChecks[@]/$check}")
        fi
      fi
    fi
  done < $report

  for mandatoryCheck in "${mandatoryChecks[@]}"; do
    if [ ! -z "$checkA" ]; then
      fails+=("Missing mandatory check : $mandatoryCheck")
    fi
  done


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
      output+="]"
  fi
  output+="}"
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
elif  [ $command == "metadata" ]; then
  getMetadata "$report"
elif  [ $command == "checkdigest" ]; then
  checkDigest "$report" "$chart"
else
  echo "{\"error\": \"$command is not a valid command\"}"
fi

