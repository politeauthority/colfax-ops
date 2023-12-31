# Colfax Ops
![Validated](https://github.com/politeauthority/colfax-ops/actions/workflows/validate.yaml/badge.svg)

Homelab GitOps on Kubernetes, powered by ArgoCD and managed by Github Actions. 🚀

## Table of Contents
- [Colfax Ops](#colfax-ops)
  - [Table of Contents](#table-of-contents)
  - [Building the Cluster from Scratch](#building-the-cluster-from-scratch)
    - [Cluster Build Steps](#cluster-build-steps)
    - [Cluster Configuration](#cluster-configuration)
  - [Cluster Management](#cluster-management)
    - [Current Applications](#current-applications)

## Building the Cluster from Scratch
This virtual Kubernetes build consists of a 1 machine running Proxmox with 15 cores and 48 gigs of
ram. This machine will be split into 3 VMs, 1 control plane and 2 worker nodes. These virtual
machines will be managed with terraform and ansible.
Eventually another worker node will be added through Vagrant and managed through ansible as well.

### Cluster Build Steps
Much of the initial cluster setup has been modified from this repo, but updated for more modern
versions of Kubernetes and modified Ansible playbooks.

 - Run `virtual-k8s/promox-k8s/proxmox/terraform` against Promox server, setting up 1 
   control-plane and 2 worker nodes. The apply takes about 4.5 minutes.

   ✏️ **Confgiruation Edits**
   - In the Terraform [variables.tf](virtual-k8s/proxmox-k8s/proxmox/terraform/variables.tf) file, 
    you'll want to update the the variables here with connection info to your Proxmox api.

   - You also may want to change IP address and the virtual machine specs in the 
    [main.tf](virtual-k8s/proxmox-k8s/proxmox/terraform/main.tf) file to suit your needs.

   In the [virtual-k8s/proxmox-k8s/proxmox/terraform/](virtual-k8s/proxmox-k8s/proxmox/terraform/) 
   directory, run the following.
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
 - Once the Terraform apply completes we'll need to setup the Ansible inventory with the nodes we
   created via Terraform. [virtual-k8s/proxmox-k8s/](virtual-k8s/proxmox-k8s/ansible/inventory.yaml)
 - This will install kubeadm and other utilities necisarry for standing up the cluster. From the
   [virtual-k8s/proxmox-k8s/proxmox/](virtual-k8s/proxmox-k8s/proxmox/) directory run the following.
   ```bash
   ansible-playbook -i ansible/inventory.yaml ansible/bootstrap.yaml -K
   ```
   ⚠️ This step will generate your first kube config, make sure to properly manage the `admin.conf`
   file.

### Cluster Configuration
- Install MetalLB through ansible, for whatever reason this works better than anything else. MetalLB
  allows us to establish an IP range we can later use as `LoadBalancer`` IP addresses.
  ```bash
  ansible-playbook -i ansible/inventory.yaml ansible/metallb.yaml -K
  ```
- Install Kube Seal, follow the [README.md](cluster/bedrock/kube-seal/README.md)
- Installed ArgoCD, follow the [README.md](cluster/argocd/README.md).

## Cluster Management
Cluster applications are managed through ArgoCD. Most applications target the `main` branch of this
repo. For more information on setting up a new ArgoCD app, check out the local
[ArgoCD README.md](cluster/argocd/README.md).

### Current Applications
| App          | In Use    | Auto Sync Enabled |
|--------------|-----------|------------|
| [**ArgoCd**](cluster/argocd/README.md) | ✅ | ✅ |
| [**Cert Manager**](cluster/bedrock/cert-manager/) | ✅ | ✅ |
| [**Ingress Private**](cluster/bedrock/ingress/ingress-private/) | ✅ | ✅ |
| [**Ingress Public**](cluster/bedrock/ingress/ingress-public) | ✅ | ✅ |
| [**Loki**](cluster/bedrock/loki/) | ⛔️ | ⛔️ |
| [**NFS-Client**](cluster/bedrock/storage/nfs-client/) | ✅ | ✅ |
| [**Prometheus Stack**](cluster/bedrock/monitoring/prometheus-stack/README.md) | ✅ | ✅ |
| **DynDNS** | ✅ | ✅ |
| [**Github Runners**](cluster/sandbox/github-runners/README.md) | ✅ | ✅ |
