# PostgreSQL helm chart

This repository contains helm chart for PostgreSQL image build and deployed on OpenShift.

For more information about helm charts see the offical [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## How to start with helm charts

The first download and install Helm. Follow instructions mentioned [here](https://helm.sh/docs/intro/install/).

## Prerequisite for PostgreSQL-persistent helm chart
Before deploying helm chart to OpenShift, you have to create a package for postgresql-imagestream.
See details [postgresql-imagestreams](../postgresql-imagestreams/README.md)


## How to work with PostgreSQL-persistent helm chart

The default PostgreSQL helm chart configuration is for RHEL7 PostgreSQL version 10.

This can be done by command:

```commandline
$ helm package ./
```

that will create a helm package named, `postgresql-persistent-0.0.2.tgz` in this directory.

The next step is to upload Helm Chart to OpenShift. This is done by command:

```commandline
$ helm install postgresql-persistent postgresql-persistent-0.0.2.tgz
```

In case you would like to use this helm chart for different versions and even RHEL versions.
you need to modify installing command.

E.g. For RHEL8

```commandline
$ helm install postgresql-persistent postgresql-persistent-0.0.2.tgz --set image.repository=registry.redhat.io/rhel8/postgresql-13 --set image.version=13
```
The values that can be overwritten are specified in file [values.yaml](./values.yaml)

To test in PostgreSQL helm chart is working properly run command:

```commandline
$ helm test postgresql-persistent --logs
```
that will print output like:
```commandline
NAME: postgresql-persistent
LAST DEPLOYED: Mon Mar 27 09:36:23 2023
NAMESPACE: pgsql-13
STATUS: deployed
REVISION: 1
TEST SUITE:     postgresql-persistent-connection-test
Last Started:   Mon Mar 27 09:37:13 2023
Last Completed: Mon Mar 27 09:37:19 2023
Phase:          Succeeded

POD LOGS: postgresql-persistent-connection-test
postgresql-testing:5432 - accepting connections
```
## Troubleshooting
For case you need a computer readable output you can add to command mentioned above option `-o json`.

In case of installation failed for reason like:
```commandline
// Error: INSTALLATION FAILED: cannot re-use a name that is still in use
```
you have to uninstall previous PostgreSQL Helm Chart by command:

```commandline
$ helm uninstall postgresql-persistent
```


