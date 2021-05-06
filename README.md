# OpenShift Helm Charts

OpenShift Helm Charts is a repository hosting [Helm Charts](https://github.com/helm/helm) available by default with [OpenShift](https://www.openshift.com/). It contains popular technologies, tools and services. Helm Charts on this repository can be provided by the community, by partners or Red Hat. 

Charts go through an automated RedHat OpenShift certification workflow, which garanties security compliance as well as best integration and experience with the platform.

## Structure of the repository

```
.
└── charts
    └── partners
        └── <entity>
            └── <chart-name>
                └── <version>
                    └── src
                        ├── Chart.yaml
                        ├── README.md
                        ├── templates
                        │   ├── deployment.yaml
                        │   ├── _helpers.tpl
                        │   ├── hpa.yaml
                        │   ├── ingress.yaml
                        │   ├── NOTES.txt
                        │   ├── serviceaccount.yaml
                        │   ├── service.yaml
                        │   └── tests
                        │       └── test-connection.yaml
                        ├── values.schema.json
                        └── values.yaml
```

Where entity is the name of the company, chart-name a unique name for the chart in this repo, and version the current version of the chart. The chart can also be packaged using the following command:

```bash
$ helm package ./<chart-name>
```

Package can then be placed directly under `./charts/partners/<entity>/<chart-name>/<version>` for example: `./charts/partners/redhat/my-awsome-chart/0.1.2/my-awsome-chart-0.1.2.tgz`.

## OpenShift Certification Program

The certification program is a great opportunity to not only double check the integrity of the charts but also use some additional testing resources. Static verification logic will run first and then actual chart testing can be run against real OpenShift clusters. If partners prefer to run the test on their own clusters, the certification program allows for that via a test report submission. 

### Contributing Helm Charts 

Interested in getting your helm charts RedHat OpenShift certified? read the [certification documention](https://github.com/openshift-helm-charts/charts/tree/main/docs)

## Installation

This repository comes configured by default starting with OpenShift 4.8. For earlier version of OpenShift or other Kubernetes distributions, the following command allows you to download and install all the charts from this repository via helm CLI:

```bash
$ helm repo add openshift-helm-charts https://helm-charts.openshift.io/
```

Helm is also integrated in the [odc web terminal](https://docs.openshift.com/container-platform/latest/web_console/odc-about-web-terminal.html), you can use the helm CLI directly from there if you installed it.

To install the repo to be used from the OpenShift console run the following command as and OpenShift admin:
```bash
$ oc apply -f https://helm-charts.openshift.io/openshift-charts-repo.yaml
```

## Using Helm

Once this repository is available and configured, Helm Charts will be available in the [OpenShift Developer Perspective](https://docs.openshift.com/container-platform/latest/applications/application_life_cycle_management/odc-working-with-helm-charts-using-developer-perspective.html)

You can also use Helm CLI commands, please refere to [Using Helm Guide](https://helm.sh/docs/intro/using_helm/) for detailed instructions on how to use the Helm client.
