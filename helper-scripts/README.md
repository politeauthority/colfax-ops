# helper-scripts

One-off operational scripts. Each one is run by hand from a machine already
authenticated to the cluster; nothing here is reconciled by ArgoCD.

| Script | What it does |
|---|---|
| `remove-pod-finalizers.sh` | Unstick a pod whose finalizer is holding it in Terminating. |
| `update-gha-token.sh` | Re-seal the GitHub Actions runner token. |
| `rotate-registry-secrets.py` | Re-key every image pull secret onto a new registry hostname. |

## rotate-registry-secrets.py

A `kubernetes.io/dockerconfigjson` secret is an `auths` map keyed by registry
*hostname string*. The kubelet takes the host off the image reference and looks
it up in that map — no fuzzy matching, no comparison by IP. So when Harbor
started answering on `harbor.alix.lol` (see #52), every secret keyed on
`harbor.squid-ink.us` stopped matching and pulls fell back to anonymous, which
Harbor refuses for every repository including the `docker-hub/` and `ghcr/`
proxy caches.

```bash
./rotate-registry-secrets.py                    # dry run, whole cluster
./rotate-registry-secrets.py -n stocky          # dry run, one namespace
./rotate-registry-secrets.py --apply -n stocky  # write, one namespace
```

Dry run is the default. Three things it will not do:

- **Write a credential it has not proved.** Every distinct robot account is
  tested against the new host first — basic auth for a pull-scoped token, then a
  real manifest GET, because Harbor issues an unscoped token to a bad credential
  and the refusal only shows up on the manifest. A secret whose credential
  cannot pull is reported and skipped, not rewritten into a differently-broken
  state.
- **Touch a sealed secret.** Some pull secrets are reconciled from git. A
  `kubectl apply` would hold until the controller resyncs and then revert, which
  is worse than not trying — the pulls would work just long enough to look
  fixed. Those are listed with the `kubeseal` command to regenerate them.
- **Restart anything.** A running pod already has its image; the secret is only
  read at the next pull. The script prints which workloads use each secret and
  stops there.

The old hostname is kept in the map alongside the new one, so a secret keeps
working if the `*.squid-ink.us` wildcard is ever repaired.

Replacing a robot account that no longer works — credentials come from the
environment, not argv, where they would show up in `ps`:

```bash
ROTATE_USERNAME='robot$k8s' ROTATE_PASSWORD='...' \
    ./rotate-registry-secrets.py --apply --replace-user 'robot$k8s'
```

Every secret it modifies is copied to `~/.registry-rotation-backup/<timestamp>/`
first.
