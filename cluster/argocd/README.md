# ArgoCD

## To Do
⚠️ `argocd/base/upstream.yaml` has a hack at line 17,649. The `--insecure` and `--loglevel` flag need
to be added as a patch.

## Fresh Install
ArgoCD has to be manually installed at first on the cluster.
I used this guide to get started. https://www.frakkingsweet.com/letting-argo-cd-manage-itself/

- In the `clusters/colfax/argocd/base` directory run
  ```bash
  cd clusters/colfax/argocd/base
  kubectl create ns argocd
  kustomize build . | kubectl apply -f -
  ```
- Port forward into ArgoCD server on port 80. (SSL is disabled in this current setup). Get the admin
  password from the secret `argocd-initial-admin-secret`.
- In the ArgoCD UI add a repository for this repo `git@github.com:politeauthority/clusters.git` and
  create a new key in the Github UI.
- Apply the entire ArgoCD kustomize, including the apps. Do this in the `argocd` namespace.
  ```bash
  cd clusters/colfax/argocd
  kustomize build . | kubectl apply -f -
  ```
- Apply the CertManager Issuers manually [colfax/bedrock/cert-manager/issuers](../cert-manager/issuers).
-  Manually install the Prometheus Operator CRDS (for some reason they dont install with kustomize).
   https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack
- Sync Prometheus Stack in the ArgoCD UI.

### AutoDeploy
Currently we auto sync the following apps. On Initial roll this can be a struggle.
  - ArgoCD
  - Fluentbit
  - Ingress Private
  - Ingress Public
  - NFS Client
⚠️ The following bedrock ArgoCD apps will have to be installed manually, in this order.
 - Cert-Manager
 - Monitoring
 

## Creating a new ArgoCD App
 - Create a file `clusters/argocd/apps/my-new-app.yaml`
 - Add it to `clusters/argocd/kustomization.yaml`


### Creating a Helm ArgoCD Package
Guide to adding a 3rd party helm chart as an ArgoCD application.
Download the remote chart and get the version
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/kube-prometheus-stack  # Get the Chart version numbers
helm show values  prometheus-community/kube-prometheus-stack > ./monitoring/values.yaml # Get the Chart values
```

Create the `Chart.yaml`
```yaml
apiVersion: v2
name: Prometheus
description: A Helm chart for Kubernetes
type: application
version: 0.0.1
appVersion: 0.0.1

dependencies:
- name: prometheus-community/prometheus
  repository: https://prometheus-community.github.io/helm-charts
  version: 22.6.6
```

#### Debugging a helm template
```bash
helm dependency build
helm template . -f values.yaml
helm template . -f values-colfax.yaml
```

### Creating a Kustomize App
A good example is Sonarr. Look at the following,
 - colfax/sonarr
 - colfax/argocd/apps/sonarr.yaml
#### Debugging a Kustomize app
```bash
kustomize build | kubectl apply —-dry-run=server -n sonarr -f 
```

## Deleting an ArgoCD app
### Kustomize
```
kustomize build . | kubectl delete --dry-run=server -n cert-manager -f -
kustomize build . | kubectl delete -n cert-manager -f -
```
## Adding Ingress
How DNS is going to be ultimately handled is still to be seen, so for now we're going 
  - just locally hacking in on MacOS `private/etc/hosts/` and run 
  - `sudo killall -HUP mDNSResponder`


