# Mac Worker Node Setup

Add a temporary Kubernetes worker node running on a local Mac via Colima + Docker.

## Context

- Cluster: kubeadm, v1.34.1
- CNI: Calico
- Control plane: 192.168.50.60
- Existing workers: colfax-1 (50.77), colfax-2 (50.76), hoyt-1 (50.79)
- Mac constraint: Docker containers on macOS are behind Docker Desktop's NAT — the control plane cannot reach them. Solution: Colima with `--network-address` puts the Docker VM on the physical LAN.

---

## Step 1 — Install Colima and Docker CLI

```bash
brew install colima docker
```

---

## Step 2 — Start Colima with bridged networking

```bash
colima start --network-address --cpu 4 --memory 8 --disk 40
```

Verify the VM has a LAN IP:

```bash
colima list
```

The VM should have a `192.168.50.x` address assigned via DHCP. Confirm it can reach the control plane:

```bash
colima ssh -- ping -c 3 192.168.50.60
```

---

## Step 3 — Fix missing systemd-resolve path

The Colima VM doesn't have `/run/systemd/resolve/resolv.conf` which kubelet requires for pod sandboxes:

```bash
colima ssh -- sudo mkdir -p /run/systemd/resolve
colima ssh -- sudo ln -s /etc/resolv.conf /run/systemd/resolve/resolv.conf
```

---

## Step 4 — (Skipped) Run the worker node container

```bash
docker run -d \
  --name mac-worker \
  --privileged \
  --network host \
  --pid host \
  -v /lib/modules:/lib/modules:ro \
  -v /sys/fs/cgroup:/sys/fs/cgroup \
  kindest/node:v1.34.0
```

- `--privileged` — required for kubelet
- `--network host` — uses the Colima VM's host network (the LAN-routable IP)
- `--pid host` — required for cgroup management

---

## Step 5 — Generate a join token

From your workstation:

```bash
ssh ubuntu@192.168.50.60 "sudo kubeadm token create --print-join-command --ttl 2h"
```

Tokens expire after 2 hours. If the node needs to rejoin, generate a new one.

---

## Step 6 — Join the cluster

```bash
docker exec -it mac-worker bash

kubeadm join 192.168.50.60:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

Verify from workstation:

```bash
kubectl get nodes
# mac-worker should appear as Ready within ~60s
```

---

## Step 7 — (Optional) Label the node

```bash
kubectl label node mac-worker node-role.kubernetes.io/worker=worker
kubectl label node mac-worker location=mac-local
```

To target workloads at this node:

```yaml
nodeSelector:
  location: mac-local
```

Or to keep workloads off this node when not needed:

```bash
kubectl cordon mac-worker
```

---

## Cleanup

Drain and remove the node gracefully:

```bash
kubectl drain mac-worker --ignore-daemonsets --delete-emptydir-data
kubectl delete node mac-worker
docker rm -f mac-worker
colima stop
```

---

## Notes

- The node is ephemeral — nothing should rely on it being permanently available
- Stateful workloads (PVCs) will not migrate automatically; drain before stopping
- Colima VM IP changes on restart — if the node loses connectivity, drain + rejoin
- Match `kindest/node` image tag to the cluster server version (`kubectl version`)
