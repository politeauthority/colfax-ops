#!/bin/bash
# Update the sealed secret for a GHA token
# This must be run on a machine which is authorized to the k8s cluster and kubeseal
# 
TOKEN=$1
echo -n ${TOKEN} \
    | kubectl create secret generic controller-manager --dry-run=client --from-file=github_token=/dev/stdin -o yaml >mysecret.yaml
kubeseal -oyaml <mysecret.yaml >../cluster/sandbox/github-runners/overlay/sealed-secret-gha-pat.yaml
rm mysecret.yaml