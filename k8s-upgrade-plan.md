# Kubernetes Upgrade Plan: v1.28.2 → v1.32.0

*Because running 4 versions behind is giving "I'll update it later" energy*

## What We Already Did (You're Welcome)

- [x] `group_vars/all` - K8s 1.32.0, containerd 1.7.24, crictl 1.32.0, runc 1.2.3
- [x] `kubeadm.yaml` - Renamed `master` to `control-plane` because it's 2025
- [x] Helm charts updated (ingress-nginx 4.11.3, prometheus-stack 66.3.0, fluent-bit 0.48.0, loki 2.10.2, harbor 1.16.0)
- [x] Calico CNI updated (v3.26.1 → v3.28.2)
- [x] MetalLB updated (v0.13.7 → v0.14.9, yeeted those PSP RBAC rules into the sun)
- [x] Helm dependency updates - done
- [x] Validation (`task check-k`, `task check-helm`) - passed, obviously

## Breaking Changes (The Drama)

### kube-prometheus-stack (47.0.0 → 66.3.0)

Skipped 19 versions. CRD updates? ArgoCD handles it automatically via `ServerSideApply=true`. We're not animals running manual kubectl commands.

### MetalLB (0.13.7 → 0.14.9)

- Control plane nodes won't advertise anymore (they have boundaries now)
- Distroless images because less attack surface = fewer 3am pages
- FRR 9.1.0 - the network is networking

### ingress-nginx (4.7.1 → 4.11.3)

- HPA API drama from `v2beta2` to `v2` - already handled, stay calm
- Controller v1.11.3 - new controller, who dis?

## Things That Just Work (Shocking, I Know)

- ArgoCD - unbothered
- Cert-manager v1.12.0 - still slaying
- OpenEBS - already on v1 snapshot APIs like a responsible citizen
- All values-colfax.yaml files - zero deprecated options, we stan

## The Upgrade (Try Not to Break Prod)

1. ~~Run `helm dependency update`~~ Already done, keep up
2. ~~Validate with `task check-k` and `task check-helm`~~ Also done
3. Commit this branch and take a deep breath
4. Deploy to staging first (yes, actually do this)
5. Run Ansible playbook for rolling node upgrade
6. Watch Grafana like a hawk
7. Merge to main, let ArgoCD cook
8. Pretend you weren't nervous the whole time
