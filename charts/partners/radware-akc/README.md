# Helm Charts for AKC - Alteon Kubernetes Controller version 1.8.0

> AKC Monitors K8S services and nodes on multiple clusters and automatically updates Alteon SLB configuration.

## Prerequisites

Kubernetes 1.24.2

Helm 3+

## Install Chart

```console
$ helm install [RELEASE_NAME] [helm package name]
```
### Example:

```console
$ helm install radware-akc akc-1.0.0_8.tgz
```

## Uninstall Chart

```console
$ helm uninstall [RELEASE_NAME]
```
### Example:

```console
$ helm uninstall radware-akc
```

## Upgrading Chart

```console
$ helm upgrade --install [RELEASE_NAME] [helm package name]
```

### Example:

```console
$ helm upgrade --install radware-akc akc-1.0.0_8.tgz
```

## Configuration

> The AKC consists of 3 sub components, the Aggregator, Controller and Configurator. User can install the aggregator, configurator and controller components together or only the controller.
### Examples:

```console
#only install the controller
$ helm install [RELEASE_NAME] [helm package name] --set controller.enabled=true
```
```console
#install all components - aggregator, configurator and controller
$ helm install [RELEASE_NAME] [helm package name] --set controller.enabled=true --set aggregator.enabled=true --set configurator.enabled=true
```

## Set Options

### Global set options
> Options for all AKC components \
> Set with --set global.option=value

* namespace: set the namespace on which the AKC components will be installed

### Example:

```console
$ --set global.namespace=default \
 #namespace: namespace in which to install all AKC components
```

### Controller set options
> Options for the Controller \
> Set with --set controller.option=value

* image.repository: the container image repository path
* image.pullPolicy: the AKC controller pullPolicy
* image.tag: the tag of the docker image (e.g. [build number] or latest)
* uid: the identifier the controller will use when communicating with the aggregator
* aggregator_ip: the IP or host name of the AKC aggregator. 
When the controller is running on the same cluster as the aggregator , use aggregator's default service name - "akc-aggregator.[namespace].svc.cluster.local"
When the controller is running on the same cluster as the aggregator and connection encryption set to 'true', use aggregator's default service 
name - "akc-aggregator.[namespace].svc.cluster.local"

### Example:

```console
$ --set controller.aggregator_ip=akc-aggregator.default.svc.cluster.local
```

* aggregator_port: the AKC aggregator port number (Only needed when AKC controller and AKC aggregator are on different clusters). In case aggregator ip is service fqdn name port range must bee 30000-32767.
```
aggregator_port default value = 30051.
```

* controller_reconcile_period: controller reconciliation sync period (controller to re-sync with the K8S cluster)
``` 
controller_reconcile_period default value = 3600 seconds.
```

* webhook.enabled: Service parameters validation using admission controller webhook
```
default value = true
```

* controller.secret.crt: user defined SSL certificate used by webhook in base64 encoded format
* controller.secret.key: user defined SSL key used by webhook in base64 encoded format
* aggregator_port: the port of the aggregator
* args.verbose: set log verbosity level
```
default value = 1
```

* controller.grpc_conn.is_grpc_encrypted
* Enable/Disable encrypted GRPC connection to aggregator that is running on the same cluster.
* WARNING!!! Supported for single cluster configuration only
* WARNING!!! This parameter have been configured by the same value on controller and aggregator side.
```
default value = disabled
```

### Aggregator set options
> Options for the Aggregator \
> Set with --set aggregator.option=value

* image.repository: the name of the docker image
* image.pullPolicy: the AKC aggregator pullPolicy
* image.tag: the tag of the docker image (e.g. [build number] or latest)
* env.max_delay: time the aggregator waits since the first controller update till it applies the configuration to the Alteon
```
default max_delay value = 120 seconds.
```
* env.max_inactivity: time the aggregator waits since the last update from any controller till it applies the configuration to the Alteon
```
default max_inactivity value = 30 seconds.
```
* env.apply_retry: time the aggregator waits since last apply failure till it retry to apply the configuration to the Alteon
```
default apply_retry value = 600 seconds.
```
* env.reconciliation_to: The interval between reconciliation processes, in seconds. When the aggregator triggers a reconciliation process it clears its database and sends reconciliation message as check status reply to the controllers. Upon receiving this message, the controllers will send its latest config.
```
default reconciliation_to value = 43,200 seconds (12 hours).
```
* env.ageout_to: The time, in seconds, that the aggregator waits for keep-alive message from a controller before considering the controller cluster as down and removing it from its database
```
default ageout_to value = 120 seconds (2 minutes).
```
* env.assets_sync_period: The time interval, in minutes, after which the aggregator will synchronize assets with Alteon configuration.
```
default assets_sync_period value = 2 minute
```
* service.nodePort: the aggregator service's public port. Same port is used for the aggregator-controller connection, in case controller(s) from another cluster(s) is in the same system. Should be the same value as in "controller.aggregator_port", which is the external aggregator port, defined in controller of another cluster
```
default service.nodePort value = "30051"
```

* args.verbose: set log verbosity level
```
default value = 1
```

* configurator.client: Define type of configurator client (vdclient or cfgclient)
```
default client value = cfgclient
```

* aggregator.configurator.ip: the IP or host name of the AKC configurator. 
When the configurator is running on the same cluster as the aggregator , use configurator's default service name - "akc-configurator.[namespace].svc.cluster.local". In this case is_rest_encrypted=enabled is required.

* aggregator.grpc_conn.is_grpc_encrypted
* Enable/Disable encrypted GRPC connection to controller that is running on the same cluster.
* WARNING!!! Supported for single cluster configuration only
* WARNING!!! This parameter have been configured by the same value on controller and aggregator side.
```
default value = false
```

* aggregator.rest_conn.is_rest_encrypted
* Enable/Disable encrypted REST connection to configurator.
* WARNING!!! This parameter have been configured by the same value on aggregator and configurator side. 
```
default value = false
```

* aggregator.configurator.protocol
* Define HTTP or HTTPS protocol for REST messages to configurator.
* Allowed values :
* http - in case is_rest_encrypted is disabled
* https - in case is_rest_encrypted is enabled
```
default value  - No default value. Have been defined. 
```

### Configurator set options, on the Aggregator scope
> In case 'vdclient' :
    > Options for the Aggregator to configure the 'configurator' and 'ipam' (vdrect) \
    > Set with --set aggregator.configurator.option=value

    * workflow: configurator workflow name
    * pool: configurator IP pool name
    * ip: configurator ip/host name
    * port: configurator port number
    * protocol: configurator protocol (http/https)

> In case 'cfgclient' :
    > Options for the Aggregator to configure the 'configurator' (cfg) \
    > Set with --set aggregator.configurator.option=value \
    > Options for Aggregator to configure the 'ipam' (vdirect) \
    > Set with --set aggregator.ipam.option=value 

    * configurator.ip: configurator ip/host name
    * configurator.port: configurator port number
    # configurator.port default value = 30188
    * configurator.protocol: configurator protocol (http)
    * ipam.workflow: ipam workflow name
    * ipam.pool: ipam IP pool name
    * ipam.ip: ipam ip/host name
    * ipam.port: ipam port number
    * ipam.protocol: ipam protocol (http/https)

### Configurator set options
> Options for the Configurator \
> Set with --set configurator.option=value

* image.repository: the container image repository path
* image.pullPolicy: the AKC configurator pullPolicy
* image.tag: the tag of the docker image (e.g. [build number] or latest)
* loglevel: the verbosity of the logs
```
# default args.verbose value = 1
```

## Alteon parameters
* alteon.master_ip: the IP address of Alteon Master
* alteon.backup_ip: the IP address of Alteon BackUp
* alteon.adcSecretCredential: Customer Alteon's device secret name that contain Alteon's connection username and password
* alteon.user: the Alteon's username that will be saved into default "akc-alteon-device-secret". Used when alteon.adcSecretCredential not defined.
* alteon.pass: the Alteon's password that will be saved into default "akc-alteon-device-secret".  Used when alteon.adcSecretCredential not defined.
* alteon.pip: the proxy IP for the real servers (nodes), configured in Alteon by AKC
* alteon.pip_mask: the Proxy mask

### Configurator customer ADC Secret Credential 
1. Create two environment variables for username and password:

U=$(echo -n "username" | base64)
P=$(echo -n "password" | base64)

2. Create secret where the data section cotains two fields with required names 'u' - <username> and 'p'-<password>

echo "
apiVersion: v1
kind: Secret
metadata:
  name: customer-adc-secret-name
data:
  u: ${U}
  p: ${P}
" | kubectl apply --filename=- --namespace="configurator name space"

#### Configurator/IPAM Username and Password
> The configurator username/password can be set by a k8s secret reference or if not exist by aggregator set options \

> A k8s secret can be set by the following command:
```console
1. Create two environment variables for username and password:

U=$(echo -n "username" | base64)
P=$(echo -n "password" | base64)

2. Create secret where the data section cotains two fields with required names 'u' - <username> and 'p'-<password>

echo "
apiVersion: v1
kind: Secret
metadata:
  name: customer-ipam-secret-name
data:
  u: ${U}
  p: ${P}
" | kubectl apply --filename=- --namespace="configurator name space"


* configurator.rest_conn.is_rest_encrypted
* Enable/Disable encrypted REST connection to aggregator.
* WARNING!!! This parameter have been configured by the same value on aggregator and configurator side. 
```
default value = false
```
## Examples:

## Install AKC Controller
```console
$ helm install radware-akc akc-1.0.0_8.tgz \
--set global.namespace=default \
--set controller.enabled=true \
--set controller.uid=akc_remote \
--set controller.aggregator_ip=10.2.2.2 \
--set controller.aggregator_port=30051 \
--set controller.image.repository=myreposistory:8081/dev/akc-controller \
--set controller.image.tag=8 \
--set controller.controller_reconcile_period=3600 \
--set controller.webhook.enabled=true \
--set controller.secret.crt=base64 encoded certificate \
--set controller.secret.key=base64 encoded key
--set aggregator.enabled=false \
```

## Install AKC Controller, Aggregator & Configurator
```console
$ helm install radware-akc akc-1.0.0_8.tgz \
--set global.namespace=default \
--set controller.enabled=true \
--set controller.uid=akc_remote \
--set controller.aggregator_ip=akc-aggregator.default.svc.cluster.local \
--set controller.aggregator_port=30051 \
--set controller.image.repository=myreposistory:8081/dev/akc-controller \
--set controller.image.tag=8 \
--set controller.controller_reconcile_period=3600 \
--set controller.webhook.enabled=true \
--set controller.secret.crt=base64 encoded certificate \
--set controller.secret.key=base64 encoded key
--set aggregator.enabled=true \
--set aggregator.configurator.client=cfgclient \
--set aggregator.configurator.workflow=workflow \
--set aggregator.configurator.pool=pool \
--set aggregator.configurator.ip=172.18.0.2 \
--set aggregator.configurator.port=30188 \
--set aggregator.configurator.protocol=http \
--set aggregator.ipam.workflow=ipam_workflow \
--set aggregator.ipam.pool=ipam_pool \
--set aggregator.ipam.ip=localhost \
--set aggregator.ipam.port=2189 \
--set aggregator.ipam.protocol=https \
--set aggregator.ipam.user=admin \
--set aggregator.ipam.pass=radware \
--set aggregator.image.repository=myreposistory:8081/dev/akc-aggregator \
--set aggregator.image.tag=latest \
--set configurator.enabled=true \
--set configurator.alteon.master_ip=10.175.101.203 \
--set configurator.alteon.backup_ip=10.175.101.204 \
--set configurator.alteon.user=admin \
--set configurator.alteon.pass=admin1 \
--set configurator.image.repository=myreposistory:8081/dev/akc-configurator \
--set configurator.image.tag=latest
```

or Alteon's connection parameters from customer secret

```console
$ helm install radware-akc akc-1.0.0_8.tgz \
--set global.namespace=default \
--set controller.enabled=true \
--set controller.uid=akc_remote \
--set controller.aggregator_ip=akc-aggregator.default.svc.cluster.local \
--set controller.aggregator_port=30051 \
--set controller.image.repository=myreposistory:8081/dev/akc-controller \
--set controller.image.tag=8 \
--set controller.controller_reconcile_period=3600 \
--set controller.webhook.enabled=true \
--set controller.secret.crt=base64 encoded certificate \
--set controller.secret.key=base64 encoded key
--set aggregator.enabled=true \
--set aggregator.configurator.client=cfgclient \
--set aggregator.configurator.workflow=workflow \
--set aggregator.configurator.pool=pool \
--set aggregator.configurator.ip=172.18.0.2 \
--set aggregator.configurator.port=30188 \
--set aggregator.configurator.protocol=http \
--set aggregator.ipam.workflow=ipam_workflow \
--set aggregator.ipam.pool=ipam_pool \
--set aggregator.ipam.ip=localhost \
--set aggregator.ipam.port=2189 \
--set aggregator.ipam.protocol=https \
--set aggregator.ipam.user=admin \
--set aggregator.ipam.pass=radware \
--set aggregator.image.repository=myreposistory:8081/dev/akc-aggregator \
--set aggregator.image.tag=latest \
--set configurator.enabled=true \
--set configurator.alteon.master_ip=10.175.101.203 \
--set configurator.alteon.backup_ip=10.175.101.204 \
--set configurator.adcSecretCredential="customer-akc-alteon-dev-secret" \
--set configurator.image.repository=myreposistory:8081/dev/akc-configurator \
--set configurator.image.tag=latest
```


## Kubernetes objects creation

### Ingress
To create ingress-related Alteon objects, user is required to configure the ingress resource as follows:

 * Ingress

 For detailed explanation see :
 https://kubernetes.io/docs/concepts/services-networking/ingress/#ingressclass-scope

 Required parameters:

 ingressClassName: akc - This parameter have been paced to inform AKC that ingress is related to Alteon's configuration.

 See example:
```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: simple-fanout-example-1
spec:
  ingressClassName: akc
  tls:
  - hosts:
    - foo.bar.com
    secretName: my-secret
  defaultBackend:
    service:
      name: test-ingress
      port: 
        number: 80
  rules:
  - host: foo.bar.com
    http:
      paths:
      - path: /foo
        pathType: Prefix
        backend:
          service:
            name: test-ingress
            port:
              number: 80
```
Optional parameters: 
  tls
  TLS will not work on the default rule because the certificates would have to be issued for all the possible sub-domains.
  In case tls is a part of the ingress manifest, the virt service is configured as https with port 443, as well as Alteon cert group with the relevant secrets, which are attached to the relevant Alteon service configuration.
  
 * Services

For detailed explanation see :

https://kubernetes.io/docs/concepts/services-networking/service/

Service type = ClusterIP.(Alteon's recomendation)

See example:

```
apiVersion: v1 
kind: Service 
metadata:
  labels:
    app: app_name
  name: test-ingress
  namespace: default 
spec:
  ports:
    - name: https
      port: 443
      targetPort: 8443 
    - name: http
      port: 80
      targetPort: 8080
  selector:
    app: app_name
  type: ClusterIP
```

 * Pods

For detailed explanation see :
https://kubernetes.io/docs/concepts/workloads/pods/



### LB Service

  annotations:
  > Alteon's assets:  

    akc.radware.com/lb-algo: leastconns
    akc.radware.com/lb-health-check: http
    akc.radware.com/sslpol: Outbound_FE_SSL_Inspection
    akc.radware.com/cert: arcady_cert
    akc.radware.com/sideband: Sideband_1
    akc.radware.com/secpath: SecurePath_Policy_1
  > If static IP is defined , AKC will not perform IPAM's IP request.

    akc.radware.com/static-ip: "10.10.10.10"

  labels:
    AlteonDevice: "true" - Service is related to Alteon

See example:

```
apiVersion: v1 
kind: Service 
metadata:
  annotations:
    akc.radware.com/lb-algo: leastconns
    akc.radware.com/lb-health-check: http
    akc.radware.com/sslpol: Outbound_FE_SSL_Inspection
    akc.radware.com/cert: arcady_cert
    akc.radware.com/sideband: Sideband_1
    akc.radware.com/secpath: SecurePath_Policy_1
    akc.radware.com/static-ip: "10.10.10.10"
  labels:
    app: test_app
    AlteonDevice: "true"
  name: test-service-http
  namespace: default 
spec:
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: http1
      port: 81
      targetPort: 8081
  selector:
    app: test_app
  type: LoadBalancer
```

### Secrets 

  labels:
    AlteonDevice: "true" - Secret is related to Alteon

See example:

```
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
  namespace: default
  labels:
    AlteonDevice: "true"
type: kubernetes.io/tls
data:
  tls.crt: "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZPakNDQXlLZ0F3SUJBZ0lVZTZBNWRjeUpGZ1djWktNNkZ6Y2w5UHA0NXp3d0RRWUpLb1pJaHZjT
  ....
  0VSVElGSUNBVEUtLS0tLQo="
  tls.key: "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlKS2dJQkFBS0NBZ0VBcTEzYkZHVGRTVzltOFdIbFF0Wkk2Y2NXNE4rOUtadEJuTEhuaEhJN...
  VdjFQVjJ4WEpuUzNPTWlFUlFNblhQOHI5bEJ3dz09Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg=="
```