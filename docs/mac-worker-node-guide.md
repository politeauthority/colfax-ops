# Mac Worker Node — Setup Guide

How to join your Mac as a temporary worker node to the colfax cluster.

**Cluster:** kubeadm v1.34.x, Calico CNI, control plane at `192.168.50.60`
**Mac interface:** en0 (Wi-Fi) on `192.168.50.0/24`

> **Key requirement:** Use `--vm-type qemu`. The default `vz` (Apple Virtualization Framework)
> NATs all VM outbound traffic through the Mac's IP, which breaks Calico BGP and IPIP pod
> networking. QEMU's vmnet-bridged backend gives the VM a real LAN IP with no NAT.

---

## One-time setup

### 1. Install dependencies

```bash
brew install colima docker qemu
```

### 2. Start Colima with bridged networking

```bash
colima start --network-address --cpu 4 --memory 8 --disk 40 --vm-type qemu --network-mode bridged --network-interface en0
```

Verify the VM got a real LAN IP (must be `192.168.50.x`, not `192.168.64.x`):

```bash
colima list
# ADDRESS should show 192.168.50.x
```

Generate the SSH config:

```bash
colima ssh-config > /tmp/colima-ssh.conf
```

### 3. Bootstrap the VM

```bash
ssh -F /tmp/colima-ssh.conf colima "sudo swapoff -a"

ssh -F /tmp/colima-ssh.conf colima "sudo sh -c 'echo overlay > /etc/modules-load.d/k8s.conf && echo br_netfilter >> /etc/modules-load.d/k8s.conf'"
ssh -F /tmp/colima-ssh.conf colima "sudo modprobe overlay && sudo modprobe br_netfilter"
ssh -F /tmp/colima-ssh.conf colima "sudo sh -c 'echo net.bridge.bridge-nf-call-iptables=1 > /etc/sysctl.d/k8s.conf && echo net.bridge.bridge-nf-call-ip6tables=1 >> /etc/sysctl.d/k8s.conf && echo net.ipv4.ip_forward=1 >> /etc/sysctl.d/k8s.conf && sysctl --system'"
```

### 4. Install Kubernetes packages

```bash
ssh -F /tmp/colima-ssh.conf colima "sudo apt-get update -qq && sudo apt-get install -y apt-transport-https ca-certificates curl gpg"
ssh -F /tmp/colima-ssh.conf colima "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list"
ssh -F /tmp/colima-ssh.conf colima "sudo apt-get update -qq && sudo apt-get install -y kubelet kubeadm kubectl && sudo apt-mark hold kubelet kubeadm kubectl"
```

### 5. Configure containerd and kubelet

```bash
# Use systemd cgroup driver
ssh -F /tmp/colima-ssh.conf colima "sudo sh -c 'containerd config default > /etc/containerd/config.toml && sed -i s/SystemdCgroup\ =\ false/SystemdCgroup\ =\ true/ /etc/containerd/config.toml && systemctl restart containerd'"

# Fix missing resolv.conf path (required for pod sandboxes)
ssh -F /tmp/colima-ssh.conf colima "sudo mkdir -p /run/systemd/resolve && sudo ln -s /etc/resolv.conf /run/systemd/resolve/resolv.conf"

# Set node IP explicitly (replace with the VM's actual 192.168.50.x address from colima list)
COLIMA_IP=$(colima list --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['address'])" 2>/dev/null || colima list | awk 'NR==2{print $NF}')
ssh -F /tmp/colima-ssh.conf colima "sudo sh -c 'echo KUBELET_EXTRA_ARGS=--node-ip=${COLIMA_IP} > /etc/default/kubelet'"
```

### 6. Join the cluster

```bash
JOIN_CMD=$(ssh ubuntu@192.168.50.60 "sudo kubeadm token create --print-join-command --ttl 2h")
ssh -F /tmp/colima-ssh.conf colima "sudo $JOIN_CMD --node-name mac-worker"
```

### 7. Label the node

```bash
kubectl label node mac-worker node-role.kubernetes.io/worker=worker location=mac-local
```

Verify BGP is established (~60s after joining):

```bash
CALICO_POD=$(kubectl get pods -n kube-system -l k8s-app=calico-node --field-selector spec.nodeName=mac-worker -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n kube-system $CALICO_POD -- birdcl show protocols | grep Mesh
# All peers should show Established
```

---

## After a Colima restart

The resolv.conf symlink does not persist. Re-apply before using the node:

```bash
colima ssh-config > /tmp/colima-ssh.conf
ssh -F /tmp/colima-ssh.conf colima "sudo mkdir -p /run/systemd/resolve && sudo ln -s /etc/resolv.conf /run/systemd/resolve/resolv.conf 2>/dev/null; sudo systemctl restart kubelet"
```

The node IP from DHCP may change on restart. If the node shows NotReady, check:

```bash
kubectl get node mac-worker -o wide   # verify INTERNAL-IP is correct
```

If the IP changed, update kubelet and rejoin:

```bash
NEW_IP=$(colima list | awk 'NR==2{print $NF}')
ssh -F /tmp/colima-ssh.conf colima "sudo sh -c 'echo KUBELET_EXTRA_ARGS=--node-ip=${NEW_IP} > /etc/default/kubelet' && sudo systemctl restart kubelet"
```

---

## Targeting workloads at this node

```yaml
nodeSelector:
  location: mac-local
```

To pause scheduling without removing:

```bash
kubectl cordon mac-worker
kubectl uncordon mac-worker
```

---

## Cleanup

```bash
kubectl drain mac-worker --ignore-daemonsets --delete-emptydir-data
kubectl delete node mac-worker
colima stop
colima delete   # only if fully removing
```
