# OpenShift Helm Charts

OpenShift Helm Charts is a repository hosting [Helm Charts](https://github.com/helm/helm) available by default with [OpenShift](https://www.openshift.com/). It contains popular technologies, tools and services. Helm Charts on this repository can be provided by the community, by partners or Red Hat. 

Charts optionaly go through an automated RedHat OpenShift certification workflow, which garanties security compliances and 

## Structure of the repository

```
|-
|- 
|-
```

## OpenShift Certification Program

Provide Certification Content here

Interested in getting your helm charts RedHat Openshift certified? read the [certification documention](https://github.com/openshift-helm-charts/charts/blob/main/README.md)

## Installation

This repository comes configured by default starting with OpenShift 4.8. For earlier version of OpenShift or other Kubernetes distributions, the following command allows you to download and install all the charts from this repository:

```bash
$ helm repo add openshift-helm-charts http://helm-charts.openshift.io/
```


Configure custom Helm Chart repositories: https://docs.openshift.com/container-platform/4.7/cli_reference/helm_cli/configuring-custom-helm-chart-repositories.html
Helm is also integrated in the Web Terminal: https://docs.openshift.com/container-platform/4.7/web_console/odc-about-web-terminal.html so you can use the helm CLI directly from the Web Terminal if you installed it.

## Using Helm

Once this repository is available and configured, Helm Charts will be available in the [OpenShift Developer Perspective](https://docs.openshift.com/container-platform/4.7/applications/application_life_cycle_management/odc-working-with-helm-charts-using-developer-perspective.html)

You can also use Helm CLI commands, please refere to (Using Helm Guide)[https://helm.sh/docs/intro/using_helm/] for detailed instructions on how to use the Helm client.

# License

