# Sealed Secrets
This allows us to store secrets in git without them being exposed. Because this is needed for many
ArgoCD projects, we install this outside of ArgoCD, and run the helm install manually.
https://github.com/bitnami-labs/sealed-secrets

## Installing
```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets \
    -n kube-system \
    --set-string fullnameOverride=sealed-secrets-controller \
    sealed-secrets/sealed-secrets
```
ℹ️ Existing secrets will have to be regenerated anytime the KubeSeal controller is brought in new to a cluster.

## Creating a Sealed Secret
```bash
kubectl \
    create secret generic \
    <secret-name> \
    --dry-run=client \
    --from-literal=foo=bar -o yaml | \
    kubeseal \
    --controller-name=sealed-secrets-controller \
    --controller-namespace=kube-system \
    --format yaml > mysealedsecret.yaml
```
