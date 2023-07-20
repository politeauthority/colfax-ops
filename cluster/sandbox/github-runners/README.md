# Github Self Hosted Runners
⚠️ This assumes that Cert Manager is already running in the cluster. See `clusters/colfax/bedrock/cert-manager`.

Followed this Guide
https://github.com/actions/actions-runner-controller/blob/master/docs/quickstart.md

## Installing
⚠️ Right now on intial install I comment out deploying the runners, since the syncs fail on missing CRDS.

## Notes
ℹ️ As stated in the doc above, before this is applied we'll need a GH PAT secret before this can work.
```bash
kubectl create secret generic controller-manager \
    -n actions-runner-system \
    --from-literal=github_token=<muh-secret>
```
OR create a sealed secret
```bash
kubectl create secret generic controller-manager \
    -n actions-runner-system \
    --dry-run=client \
    -o yaml \
    --from-literal=github_token=<muh-secret> | \
kubeseal --format yaml > sealed-secret-gha-pat.yaml
```

ℹ️ If job's require k8s access, you'll need to base64 a kubeconfig and store it as a repo secret in Github called `KUBECONFIG`.
