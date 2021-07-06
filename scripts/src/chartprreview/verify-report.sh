#!/bin/bash

delim=G
mandatoryChecksPartner=( "${delim}v1.0/contains-test${delim}"
            "${delim}v1.0/contains-values${delim}"
            "${delim}v1.0/contains-values-schema${delim}"
            "${delim}v1.0/has-kubeversion${delim}"
            "${delim}v1.0/has-readme${delim}"
            "${delim}v1.0/helm-lint${delim}"
            "${delim}v1.0/images-are-certified${delim}"
            "${delim}v1.0/is-helm-v3${delim}"
            "${delim}v1.0/not-contain-csi-objects${delim}"
            "${delim}v1.0/chart-testing${delim}"
            "${delim}v1.0/not-contains-crds${delim}" )
mandatoryChecksRedHat=( "${delim}v1.0/contains-test${delim}"
            "${delim}v1.0/contains-values${delim}"
            "${delim}v1.0/contains-values-schema${delim}"
            "${delim}v1.0/has-kubeversion${delim}"
            "${delim}v1.0/has-readme${delim}"
            "${delim}v1.0/helm-lint${delim}"
            "${delim}v1.0/images-are-certified${delim}"
            "${delim}v1.0/is-helm-v3${delim}"
            "${delim}v1.0/not-contain-csi-objects${delim}"
            "${delim}v1.0/chart-testing${delim}"
            "${delim}v1.0/not-contains-crds${delim}" )
mandatoryChecksCommunity=( "${delim}v1.0/helm-lint${delim}" )

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
    line="$(echo -e "${line}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
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
            annotations+=("\"charts.openshift.io/digest\":\"$digest\"")
        elif [[ $line == "lastCertifiedTimestamp:"* ]]; then
            certtime=`echo "$line" | sed 's/lastCertifiedTimestamp://' | xargs`
            annotations+=("\"charts.openshift.io/lastCertifiedTimestamp\":\"$certtime\"")
        elif [[ $line == "certifiedOpenShiftVersions:"* ]]; then
            osvs=`echo "$line" | sed 's/certifiedOpenShiftVersions://' | xargs`
            annotations+=("\"charts.openshift.io/certifiedOpenShiftVersions\":\"$osvs\"")
        fi
      elif [ "$chart" = true ]; then
        if [[ $line == "annotations:"* ]]; then
            chartannotations=true
        elif [ "$chartannotations" = true ]; then
          if [[ $line == "charts.openshift.io/"* ]]; then
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
  profile=$2

  case "${profile}" in
    partner)
      mandatoryChecks=${mandatoryChecksPartner}
      ;;
    redhat)
      mandatoryChecks=${mandatoryChecksRedHat}
      ;;
    community)
      mandatoryChecks=${mandatoryChecksCommunity}
      ;;
    *)
      mandatoryChecks=${mandatoryChecksPartner}
      ;;
  esac

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
            nextlinereason=false
            check=""
            type=""
            outcome=""
            reason=""
        fi
        if [[ $line == *"check:"* ]]; then
           check=`echo "$line" | cut -d: -f2- | xargs`
        elif [[ $line == *"type:"* ]]; then
           type=`echo $line | cut -d: -f2- | xargs`
        elif [[ $line == *"outcome:"* ]]; then
           outcome=`echo $line | cut -d: -f2- | xargs`
        elif [[ $line == *"reason:"* ]]; then
           reason=`echo $line | cut -d: -f2- | xargs`
           if [[ $reason == *'|-' ]]; then
             multireason=true
             reason=""
           elif [[ $reason == *'|' ]]; then
             nextlinereason=true
             reason=""
           fi
        elif [ "$multireason" = true ]; then
          reason=`echo $line | xargs`
          if [[ $line == *"Image is Red Hat certified"* ]]; then
            outcome="PASS"
          else
            outcome="FAIL"
          fi
        elif [ "$nextlinereason" = true ]; then
          reason=`echo $line | xargs`
          nextlinereason=false
        fi

        if [ -n "$check" ] && [ -n "$type" ] && [ -n "$outcome" ] && [ -n "$reason" ]; then
          if [[ $outcome != "PASS" ]] && [[ $type == "Mandatory" ]]; then
              fails+=("$check : $reason")
          else
            passed=$((passed+1))
          fi

          remove="$delim$check$delim"
          mandatoryChecks=("${mandatoryChecks[@]/$remove}")
        fi
      fi
    fi
  done < $report

  for mandatoryCheck in "${mandatoryChecks[@]}"; do
    if [ ! -z "$mandatoryCheck" ]; then
      missingcheck="${mandatoryCheck%$delim}"
      missingcheck="${missingcheck#$delim}"
      fails+=("Missing mandatory check : $missingcheck")
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
  profile=$3
  getFails "$report" "$profile"
elif  [ $command == "annotations" ]; then
  getAnnotations "$report"
elif  [ $command == "metadata" ]; then
  getMetadata "$report"
elif  [ $command == "checkdigest" ]; then
  checkDigest "$report" "$chart"
else
  echo "{\"error\": \"$command is not a valid command\"}"
fi

