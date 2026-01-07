# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Colfax Ops is a homelab GitOps infrastructure repository managing a Kubernetes cluster through ArgoCD. The main branch is the source of truth - ArgoCD continuously syncs applications from this repository to the cluster.

**Infrastructure stack**: Proxmox VMs (Terraform) → OS bootstrap (Ansible) → Kubernetes (kubeadm + containerd + Calico) → GitOps (ArgoCD)

## Common Commands

This project uses Task (taskfile.dev) as the task runner:

```bash
task check-k      # Validate all Kustomize builds (argocd, cert-manager, github-runners, mosquitto)
task check-helm   # Validate all Helm charts (fluentbit, ingress-*, prometheus-stack, nfs-client, harbor)
```

**Infrastructure provisioning** (from `virtual-k8s/proxmox-k8s/proxmox/`):
```bash
terraform init && terraform plan && terraform apply   # Provision VMs
ansible-playbook -i ansible/inventory.yaml ansible/bootstrap.yaml -K   # Bootstrap cluster
ansible-playbook -i ansible/inventory.yaml ansible/metallb.yaml -K     # Install MetalLB
```

**Debugging templates**:
```bash
kustomize build cluster/path/to/app         # Render Kustomize
helm dependency build && helm template . -f values-colfax.yaml   # Render Helm
```

## Architecture

```
cluster/
├── argocd/                    # ArgoCD installation and Application CRDs
│   ├── base/                  # Core ArgoCD manifests
│   ├── apps/                  # Application definitions by category
│   │   ├── bedrock/           # Infrastructure (cert-manager, ingress, monitoring)
│   │   ├── homelab/           # User apps (Immich, Synapse, Home Assistant)
│   │   └── sandbox/           # Experimental (Harbor, Ollama)
│   └── overlays/              # Kustomize overlays
├── bedrock/                   # Core cluster infrastructure
│   ├── cert-manager/          # TLS certificates
│   ├── ingress/               # Nginx controllers (private + public)
│   ├── monitoring/            # Prometheus + Grafana + Loki
│   └── storage/               # NFS provisioner, OpenEBS
└── sandbox/                   # User/experimental applications

virtual-k8s/proxmox-k8s/       # Infrastructure provisioning
├── proxmox/terraform/         # VM creation on Proxmox
└── proxmox/ansible/           # Cluster bootstrap playbooks
```

## Key Patterns

**Adding a new application**:
1. Create manifests in `cluster/{category}/{app-name}/` (Kustomize or Helm wrapper)
2. Create ArgoCD Application CRD in `cluster/argocd/apps/{category}/{app-name}.yaml`
3. Add to appropriate `kustomization.yaml`
4. Validate with `task check-k` or `task check-helm`

**Helm chart wrapper pattern**: Each Helm-based app has `Chart.yaml` with upstream dependency + `values-colfax.yaml` for customization.

**Two ingress controllers**: `ingress-private` for internal services, `ingress-public` for external. Use appropriate IngressClass.

**Secrets**: Use Sealed Secrets for encrypted storage in Git.

## Important Notes

- Some apps reference `git@github.com:politeauthority/private-ops.git` (separate private repo)
- Bedrock apps (cert-manager, monitoring) often require manual sync on initial install
- MetalLB provides LoadBalancer IPs from 192.168.50.x pool
- DNS is currently manual (hosts file)
