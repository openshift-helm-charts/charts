# diffgram-helm
Helm Chart for DIffgram


Full Tutorial on Azure: https://medium.com/diffgram/tutorial-installing-diffgram-on-azure-aks-b9447685e271

# How to Install: 

## A. Pre-requisites

### Ingress Controller
If you are using minikube make sure you've done:

`minikube addons enable ingress`

To have the ingress enabled, otherwise you won't be able to acess your diffgram services from outside the cluster.

If you are not on minikube, you can use the Nginx K8s Ingress Controller. Check how to install on your cloud provider here: https://kubernetes.github.io/ingress-nginx/deploy/

### Opencore or Enterprise

Make sure you set the value of  `diffgramEdition` in the `values.yaml` to either `opencore`
or `enterprise`.

If you set the `diffgramEdition` to `enterprise` you will have to provide the GCR credentials 
Key (Provided by the Diffgram Team). And set the value on `imagePullCredentials.gcrCredentials` value inside the `values.yaml` file.
### Setting Up the Docker Registry Key (Enterprise Only):

To install the helm chart with the Enterprise Edition of Diffgram you will need to receive a GCR key with the permissions from
the Diffgram team to fetch our images.

Please Contact us if you want  to get one here:  https://diffgram.com/contact

Once you have your GCR Key please set it in the `values.yaml` file, specifically inside the
key `imagePullCredentials.gcrCredentials`.


```
imagePullCredentials:
  # The service account with permissions to pull from the GCR Repository. [Should be Provided by Diffgram Team.]
  gcrCredentials: <YOUR KEY GOES HERE>
```



### TLS Ceritificates
#### Using minikube (For local testing) 
Install Cert Manager
`helm repo add jetstack https://charts.jetstack.io`

`helm install cert-manager --namespace default jetstack/cert-manager --set installCRDs=true`

Default domain on diffgram is: `example.com` so make sure you add that to your local hosts file:

`echo "$(minikube ip) example.com" | sudo tee -a /etc/hosts`

#### Using cert-manager             

1. If you want to have TLS connections, please make sure you have a domain available and access to the name servers so you can modify the records to point to the IP addresses of the ingress.

`helm repo add jetstack https://charts.jetstack.io`

`helm install cert-manager --namespace default jetstack/cert-manager --set installCRDs=true`

2. Now edit the values.yaml of Diffgram’s helm chart and change the following keys:
 - **diffgramDomain:** set it to the domain you own.
 - **useCertManager:** set this to true. This will allow the certificate issue to be created so you can automatically get a TLS certificate for your domain with let’s encrypt.

3. Reinstall the helm chart


`helm upgrade diffgram -f diffgram/new_updated_values_from_above_step.yaml`

4. After a few minutes you should be able to see the issuer and the certificate generated. You can confirm this by running:
`kubectl describe issuer letsencrypt-prod`

## B. Installation
`git clone https://github.com/diffgram/diffgram-helm/`

`helm install diffgram ./diffgram-helm --create-namespace`

If you don't change anything on `values.yaml`. You will have the namespace `default` created on your cluster

Note: if on Minikube: run `echo "$(minikube ip) example.com" | sudo tee -a /etc/hosts`

To point minikube to domain example.com (or whatever domain you have set in the `diffgramDomain` inside `values.yaml`

### Values to Change in `values.yaml`
Check section D. to see required values.



You can substitute `./diffgram-helm` with whatever the path to this repo is on your local machine. Also feel free to install on any other namespace.

Future versions will provide a repo to download the chart without cloning from github.

## C. Main Structure
When deploying this chart there are 5 main components to be aware of:

**1. default-service:** This is the service in charge for most of the API calls and data management. Both for the SDK and for the Frontend UI.

**2. walrus-service:** This is a long running service for CPU intensive processing. Things like video, splitting, huge files copying and other maintainance tasks are performed on this service

**3. frontend-service:** Static VueJS frontend for accessing Diffgram.

**4. db-service:** A PostgresSQL database, we usually recommend linking an external managed cloud service like AWS RDS, GCP SQL Service, or Azure Managed SQL Service.

**5. ingress:** A Nginx ingress controller for accessing all the services. This is the entry point and router to all the above services.


## D. Configurations:
The following are some of the most important configurations of the values.yaml in the helm chart. Please feel free to contact us if you have any questions on any of the configurations.
## 4.1 Database Settings
**1. dbSettings.dbProvider:** Set this to “rds”, "azure", or "local" depending on your DB managed service.

**2. dbSettings.rdsEndpoint:** Set this to your RDS instance endpoint, so diffgram can use it as the database.

**3. dbSettings.dbProvider:** Set this to “rds”

**4, dbSettings.dbUser:** Set this to the postgres user you want to use with Diffgram.

**5. dbSettings.dbName:** Set this to Postgres Database name you want to create the tables on

**6. dbSettings.dbPassword:** Set this to RDS instance’s password

## 4.2 Diffgram Configuration Settings
**1. diffgramSecrets.DIFFGRAM_STATIC_STORAGE_PROVIDER:** Set this to “aws”, "azure", or "gcp" depending on your DB managed service. Default is `aws`
**1. diffgramSecrets.DIFFGRAM_AWS_ACCESS_KEY_ID:** Set this to your AWS credentials access key. Make sure the account has permissions to the S3 bucket you’ll use as static storage.

**2. diffgramSecrets.DIFFGRAM_AWS_ACCESS_KEY_SECRET:** Set this to your AWS credentials secret. Make sure the account has permissions to the S3 bucket you’ll use as static storage.

**3. diffgramSettings.DIFFGRAM_S3_BUCKET_NAME:** Set this to your S3’s bucket name for static file storage.

**4. diffgramSettings.ML__DIFFGRAM_S3_BUCKET_NAME:** Set this to your S3’s bucket name for static file storage.

## E. Common Issues:

1. My Helm Chart gets stuck during install and the timesout with 

Try doing `kubectl get pods` and find a pod named `diffgram-pre-install-{SOME-ID}`.

Now do `kubectl logs diffgram-pre-install-{SOME-ID} -c pre-upgrade-alembic-hook`

This will show the logs of the POD to further debug the issue. Most common causes for this error are:

- Missing Blob Storage Provider Credentials (Either AWS Access Keys, GCP Service Account or Azure Conn String)


