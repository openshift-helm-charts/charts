# PostgreSQL Helm Chart imagestreams

The file contains all supported PostgreSQL imagestreams.

For more information about helm charts see the offical [Helm Charts Documentation](https://helm.sh/).

You need to have access to a cluster for each operation with OpenShift 4, like deploying and testing.

## How to start with helm charts

The first download and install Helm. Follow instructions mentioned [here](https://helm.sh/docs/intro/install/).

## How to work with PostgreSQL helm chart

Before deploying helm chart to OpenShift, you have to create a package.
This can be done by command:

```commandline
$ helm package ./
```

that will create a helm package named, `postgresql-imagestreams-v0.0.1.tgz` in this directory.

The next step is to upload Helm Chart to OpenShift. This is done by command:

```commandline
$ helm install postgresql-imagestreams postgresql-imagestreams-v0.0.1.tgz
```

In order to check if everything is imported properly, run command:
```commandline
$ oc get is -o json
```
that will print all support PostgreSQL imagestreams.


## Troubleshooting
For case you need a computer readable output you can add to command mentioned above option `-o json`.

In case of installation failed for reason like:
```commandline
// Error: INSTALLATION FAILED: cannot re-use a name that is still in use
```
you have to uninstall previous PostgreSQL Helm Chart by command:

```commandline
$ helm uninstall postgresql-imagestreams
```


