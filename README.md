# Colfax Ops
Homelab Git Ops on Kubernetes.

## Getting A Fresh Build
This virtual Kubernetes build consists of a 1 machine running Proxmox with 15 cores and 48 gigs of
ram. This machine will be split into 3 VMs, 1 control plane and 2 worker nodes. These virtual
machines will be managed with terraform and ansible.
Eventually another worker node will be added through Vagrant and managed through ansible as well.

### Cluster Build Steps
Much of the initial cluster setup has been modified from this repo, but updated for more modern
versions of Kubernetes and modified Ansible playbooks.
 - Run `virtual-k8s/promox-k8s/proxmox/terraform` against Promox server, setting up 1 
   control-plane and 2 worker nodes. The apply takes about 4.5 minutes.

   ℹ️ **Note**
   - In the Terraform [variables](virtual-k8s/proxmox-k8s/proxmox/terraform/variables.tf) file, you'll want to update the the variables here with connection info to your Proxmox api.

    - You also may want to change IP address and the virtual machine specs in the [main.tf](virtual-k8s/proxmox-k8s/proxmox/terraform/main.tf) file to suit your needs.

   In the [virtual-k8s/proxmox-k8s/proxmox/terraform/](virtual-k8s/proxmox-k8s/proxmox/terraform/) directory, run the following.
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
 - terraform apply -var="variable_name=value"