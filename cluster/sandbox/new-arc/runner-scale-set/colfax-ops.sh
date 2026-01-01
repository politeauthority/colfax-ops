INSTALLATION_NAME="arc-colfax-ops"
NAMESPACE="arc-runners"
GITHUB_CONFIG_URL="https://github.com/politeauthority/cver"
GITHUB_PAT=""
helm upgrade "${INSTALLATION_NAME}" \
    --install  \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set \
    -f values-colfax-ops.yaml

