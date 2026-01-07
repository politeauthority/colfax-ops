# Branch Comparison: `this-stuff` vs `main`

## Summary

- **Commits ahead of main**: 1 (`993063c stuff`)
- **Files changed**: 48
- **Lines added**: +7,484
- **Lines deleted**: -223

## Changes by Category

### ArgoCD Apps

| Change | File |
|--------|------|
| Archived | `cloud-native-pg.yaml` → moved to `_archive/` (commented out) |
| Modified | `argo-workflows.yaml` - enabled auto-sync with prune |

### Bedrock Infrastructure

**cert-manager**
- Quote style changes in `cert-manager.yaml` (single → double quotes, cosmetic)
- Added to kustomization

**ingress**
- New `README.md` with ingress documentation
- New `exporter-svc.yaml` template for ingress-public metrics

**storage (new options)**
- **Longhorn**: `ingress.yaml`, `setup.md`, `test-pvc.yaml`
- **OpenEBS**: Full Helm chart setup (`Chart.yaml`, `values.yaml`, `values-colfax.yaml`, `render.yaml`, `demo.yaml`, `README.md`)

### Sandbox Applications

**argo-workflows**
- `network.yaml` - networking configuration
- `quick-start-minimal.yaml` - 1,849 lines of Argo Workflows manifests

**backup**
- `kusomization.yaml` (note: typo in filename)
- `test-deployment.yaml`

**minio** (archived)
- Full deployment in `_archive/minio/`: deployment, network-api, network-console, secrets, storage

**new-arc** (Actions Runner Controller v2)
- `runner-scale-set/colfax-ops.sh`
- `values-colfax-ops.yaml`, `values-colfax.yaml`, `values.yaml`

**ollama**
- Complete deployment: `deployment.yaml`, `network.yaml`, `storage.yaml`
- GPU support: `gpus/amd.yaml`
- `kustomization.yaml`

**rescue**
- `kustomization.yaml`
- `rescue-0.yaml`, `rescue-2.yaml` - rescue pod deployments
- `secrets-rescue.yaml`

**wordpress**
- `header.html` - custom header
- **nova-nails**: Full WordPress + MySQL stack (`kustomization.yaml`, `mysql.yaml`, `wordpress.yaml`)
- **please-no-press**: Full WordPress + MySQL stack (`kustomization.yaml`, `mysql.yaml`, `wordpress.yaml`, `secrets.yaml`)

## Notable Details

1. **OpenEBS render.yaml**: 4,097 lines - full rendered Helm output for storage
2. **Argo Workflows quick-start**: 1,849 lines - substantial workflow infrastructure
3. **Two new WordPress sites**: nova-nails and please-no-press with separate MySQL instances
4. **Ollama LLM**: Ready for deployment with AMD GPU support option
5. **New ARC runner-scale-set**: Alternative to existing github-runners setup
