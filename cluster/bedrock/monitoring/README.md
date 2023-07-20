# Install Prometheus

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts


helm upgrade --install -n quig-system prometheus prometheus-community/prometheus -f monitoring/values.yaml


# To Build
For this app we unfold the helm template, and make it a kustomize resource.

```bash
cd clusters/colfax/monitoring/prometheus-stack/helm
helm dependency build
kc-set-ns monitoring
helm template promstack . -f values-colfax.yaml > ../kustomize/base.yaml
```
