# This document is created to guide us in case we need to regenerate the test data
## It also captures traceability between tests and how the test data is generated

### HC-01, HC-02, HC-03, HC-05, HC-07, HC-08, HC-12, HC-14, HC-16

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true > report.yaml
Copy report.yaml to tests/data/common/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --set profile.vendorType=redhat > report.yaml
Copy report.yaml to tests/data/common/redhat/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --set profile.vendorType=community > report.yaml
Copy report.yaml to tests/data/common/community/

```

### HC-04

```
chart-verifier verify tests/data/common/vault-0.17.0.tgz > report.yaml
Copy report.yaml to tests/data/HC-04/partner/

chart-verifier verify tests/data/common/vault-0.17.0.tgz --set profile.vendorType=redhat > report.yaml
Copy report.yaml to tests/data/HC-04/redhat/

chart-verifier verify tests/data/common/vault-0.17.0.tgz --set profile.vendorType=community > report.yaml
Copy report.yaml to tests/data/HC-04/community/
```

### HC-06

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --provider-delivery > report.yaml
Copy report.yaml to tests/data/HC-06/partner/
```

### HC-09

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true -o json | jq . > report.json
Copy report.json to tests/data/HC-09/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --set profile.vendorType=redhat -o json | jq . > report.json
Copy report.json to tests/data/HC-09/redhat/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --set profile.vendorType=community -o json | jq . > report.json
Copy report.json to tests/data/HC-09/community/
```

### HC-11

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true -x helm-lint > report.yaml
Copy report.yaml to tests/data/HC-11/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true -x not-contains-crds > report.yaml
Copy report.yaml to tests/data/HC-11/partner_not_contain_crds/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true --set profile.vendorType=community -x helm-lint > report.yaml
Copy report.yaml to tests/data/HC-11/community/
```

### HC-17

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/psql-service-0.1.10-1.tgz?raw=true > report.yaml
Copy report.yaml to tests/data/HC-17/dash-in-version/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/psql-service-0.1.10-1.tgz?raw=true --set profile.vendorType=redhat > report.yaml
Copy report.yaml to tests/data/HC-17/dash-in-version/redhat/
```

### HC-18

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.18.0.tgz?raw=true  > report.yaml
Copy report.yaml to tests/data/HC-18/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.18.0.tgz?raw=true  --set profile.vendorType=redhat > report.yaml
Copy report.yaml to tests/data/HC-18/redhat/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.18.0.tgz?raw=true  --set profile.vendorType=community > report.yaml
Copy report.yaml to tests/data/HC-18/community/

```

### HC-19

```
chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true > report.yaml
Copy report.yaml to tests/data/HC-19/report_sha_good/
Also modify the testedOpenShiftVersion value in report.yaml and copy to tests/data/HC-19/report_edited_sha_bad/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/vault-0.17.0.tgz?raw=true > report.yaml
Modify the reportDigest value itself in report.yaml and copy to tests/data/HC-19/report_sha_bad/

```

### HC-10

```
Unpack the unsigned vault-0.17.0.tgz into vault/ directory

Sign the chart using your private key and package it using below cmd:
$ helm package --sign --key 'Sushanta Das' --keyring /home/susdas/.gnupg/secring.gpg vault/
Password for key "Sushanta Das (Key generated in loaner laptop) <susdas@redhat.com>" >  
Successfully packaged chart and saved it to: /home/susdas/go/src/github.com/tisutisu/development/tests/data/HC-10/signed_chart/vault-0.17.0.tgz
$ 

Verify the resulting chart tar and .prov file should be under tests/data/HC-10/signed_chart

Also generate your public key and copy it into the same tests/data/HC-10/signed_chart directory using below cmd:
gpg --export -a susdas@redhat.com > public_key_good.asc


chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/HC-10/signed_chart/vault-0.17.0.tgz?raw=true -k tests/data/HC-10/signed_chart/public_key_good.asc > report.yaml
Copy report.yaml to tests/data/HC-10/signed_chart/report/partner/

chart-verifier verify https://github.com/openshift-helm-charts/development/blob/main/tests/data/HC-10/signed_chart/vault-0.17.0.tgz?raw=true -k tests/data/HC-10/signed_chart/public_key_good.asc --set profile.vendorType=redhat > report.yaml
Copy report.yaml to tests/data/HC-10/signed_chart/report/redhat/

```

