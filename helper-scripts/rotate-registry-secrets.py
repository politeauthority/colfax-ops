#!/usr/bin/env python3
"""Re-key every image pull secret in the cluster onto a new registry hostname.

A `kubernetes.io/dockerconfigjson` secret is an `auths` map keyed by registry
*hostname string*. The kubelet takes the host off the image reference and looks it
up in that map; there is no fuzzy matching and no comparison by IP. So when Harbor
started answering on `harbor.alix.lol`, every secret keyed on
`harbor.squid-ink.us` stopped matching, the kubelet fell back to anonymous, and
anonymous is refused for every repository including the `docker-hub/` and `ghcr/`
proxy caches.

That is what this repairs: the same credentials, filed under the new hostname.

WHY IT VERIFIES BEFORE IT WRITES. The credentials in these secrets are Harbor
robot accounts, and they do not all still work — a robot that was deleted or had
its token rotated fails just as loudly as a wrong hostname, and fails *after* you
have already overwritten the secret. So every distinct credential is proved
against the new host first (basic auth for a pull-scoped token, then a real
manifest GET), and a secret whose credential cannot pull is reported and skipped
rather than rewritten into a differently-broken state.

SEALED SECRETS ARE NOT TOUCHED. Some pull secrets are owned by a SealedSecret and
reconciled from git. Writing those with `kubectl apply` would hold until the
controller resyncs and then silently revert, which is worse than not trying: the
pulls would work long enough to look fixed. Those are listed with the `kubeseal`
command to regenerate them, and left alone.

NOTHING IS RESTARTED. A running pod keeps its image; the secret only matters at
the next pull. Which workloads would need a restart to pick it up is reported, and
that is as far as this goes.

Usage:
    ./rotate-registry-secrets.py                          # dry run, whole cluster
    ./rotate-registry-secrets.py -n stocky -n stocky-work # dry run, two namespaces
    ./rotate-registry-secrets.py --apply                  # write
    ./rotate-registry-secrets.py --apply -n stocky        # write, one namespace

To supply a replacement credential for a robot that no longer works, put it in the
environment rather than on the command line, where it would show up in `ps`:

    ROTATE_USERNAME='robot$k8s' ROTATE_PASSWORD='...' \
        ./rotate-registry-secrets.py --apply --replace-user 'robot$k8s'
"""

import argparse
import base64
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

OLD_HOST = "harbor.squid-ink.us"
NEW_HOST = "harbor.alix.lol"

#: Repositories a credential is proved against. One private project and both proxy
#: caches, because they are separate Harbor projects with separate access rules: a
#: robot that can pull `politeauthority/` may still be refused `docker-hub/`, and
#: base images come from there.
PROBE_REPOS = (
    "politeauthority/stocky-api",
    "docker-hub/library/postgres",
    "ghcr/astral-sh/uv",
)

DOCKERCONFIG_TYPE = "kubernetes.io/dockerconfigjson"
CONFIG_KEY = ".dockerconfigjson"


def kubectl(*args, check=True):
    """Run kubectl and return stdout, or raise with the stderr on the exception."""
    proc = subprocess.run(("kubectl",) + args, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError("kubectl %s failed: %s" % (" ".join(args), proc.stderr.strip()))
    return proc.stdout


def load_pull_secrets(namespaces):
    """Every dockerconfigjson secret, as (namespace, name, parsed auths, raw object)."""
    args = ["get", "secrets", "--field-selector", "type=" + DOCKERCONFIG_TYPE, "-o", "json"]
    if namespaces:
        out = []
        for ns in namespaces:
            out.extend(json.loads(kubectl(*(args + ["-n", ns])))["items"])
        items = out
    else:
        items = json.loads(kubectl(*(args + ["--all-namespaces"])))["items"]

    secrets = []
    for item in items:
        raw = (item.get("data") or {}).get(CONFIG_KEY)
        if not raw:
            # A dockerconfigjson secret with no config in it is somebody's stub. It
            # cannot be re-keyed and inventing one would be worse than saying so.
            continue
        try:
            config = json.loads(base64.b64decode(raw))
        except (ValueError, TypeError):
            config = None
        secrets.append(
            {
                "namespace": item["metadata"]["namespace"],
                "name": item["metadata"]["name"],
                "config": config,
                "item": item,
            }
        )
    return secrets


def sealed_owned(namespaces):
    """(namespace, name) pairs that a SealedSecret reconciles.

    Matched on namespace and name rather than on ownerReferences: the controller
    does set an owner reference, but a secret it has not reconciled yet has none
    while still being git-managed, and rewriting that one is the same mistake.
    """
    try:
        args = ["get", "sealedsecrets", "-o", "json"]
        if namespaces:
            items = []
            for ns in namespaces:
                items.extend(json.loads(kubectl(*(args + ["-n", ns]), check=False) or '{"items":[]}')["items"])
        else:
            items = json.loads(kubectl(*(args + ["--all-namespaces"]), check=False) or '{"items":[]}')["items"]
    except (RuntimeError, ValueError):
        # No SealedSecret CRD, or no permission to list them. Treat nothing as
        # sealed and say so, rather than silently skipping everything.
        print("  ! could not list SealedSecrets — treating all secrets as hand-applied")
        return set()
    return {(i["metadata"]["namespace"], i["metadata"]["name"]) for i in items}


def probe_credential(username, password, host, repos=PROBE_REPOS, timeout=15):
    """Prove a credential can actually pull from `host`.

    Does what the kubelet does rather than something adjacent to it: basic auth for
    a pull-scoped bearer token, then a real manifest GET. A token endpoint that
    answers 200 proves nothing on its own — Harbor issues an unscoped token to a
    bad credential, and the refusal only shows up on the manifest.

    Returns (ok, detail).
    """
    accept = ",".join(
        (
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
            "application/vnd.docker.distribution.manifest.v2+json",
        )
    )
    basic = base64.b64encode(("%s:%s" % (username, password)).encode()).decode()
    failures = []
    for repo in repos:
        scope = urllib.parse.quote("repository:%s:pull" % repo)
        token_url = "https://%s/service/token?service=harbor-registry&scope=%s" % (host, scope)
        try:
            req = urllib.request.Request(token_url)
            req.add_header("Authorization", "Basic " + basic)
            token = json.load(urllib.request.urlopen(req, timeout=timeout)).get("token", "")
        except urllib.error.HTTPError as exc:
            failures.append("%s: token HTTP %s" % (repo, exc.code))
            continue
        except Exception as exc:  # noqa: BLE001 - a probe must not kill the run
            failures.append("%s: token error %s" % (repo, exc))
            continue

        try:
            req = urllib.request.Request("https://%s/v2/%s/manifests/latest" % (host, repo))
            req.add_header("Authorization", "Bearer " + token)
            req.add_header("Accept", accept)
            urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            # 404 is a pass: the credential was accepted and the repository simply
            # has no `latest`. 401/403 is the refusal this is looking for.
            if exc.code != 404:
                failures.append("%s: manifest HTTP %s" % (repo, exc.code))
        except Exception as exc:  # noqa: BLE001
            failures.append("%s: manifest error %s" % (repo, exc))

    return (not failures), "; ".join(failures) if failures else "all probes ok"


def rekey(config, old_host, new_host, replacement=None):
    """Move old-host auths onto the new host. Returns (new_config, username) or None.

    The `auth` field is base64("user:pass") and carries no hostname, so the entry
    moves across whole. Other hosts in the map are left exactly as they are — a
    secret that also holds a Docker Hub or ghcr.io credential keeps it.

    The old entry is kept. Harbor still answers on the old name once its DNS is
    repaired, and a secret that can pull from either host is strictly better than
    one that has to be rotated again if the wildcard comes back.
    """
    auths = dict((config or {}).get("auths") or {})
    if old_host not in auths:
        return None
    entry = dict(auths[old_host])
    username = entry.get("username")
    if replacement:
        user, password = replacement
        entry["username"] = user
        entry["password"] = password
        entry["auth"] = base64.b64encode(("%s:%s" % (user, password)).encode()).decode()
        username = user
    auths[new_host] = entry
    out = dict(config or {})
    out["auths"] = auths
    return out, username


def backup(secrets, directory):
    """Write each secret's live manifest out before anything is changed."""
    os.makedirs(directory, exist_ok=True)
    for s in secrets:
        path = os.path.join(directory, "%s.%s.json" % (s["namespace"], s["name"]))
        with open(path, "w") as handle:
            json.dump(s["item"], handle, indent=2)
        os.chmod(path, 0o600)
    return directory


def workloads_using(namespace, secret_name):
    """Pods currently mounting this pull secret, as owner names.

    Reported, never acted on. A running pod already has its image; the secret is
    only read at the next pull. Restarting is the operator's call.
    """
    try:
        out = kubectl("get", "pods", "-n", namespace, "-o", "json", check=False)
        items = json.loads(out or '{"items":[]}')["items"]
    except (RuntimeError, ValueError):
        return []
    owners = set()
    for pod in items:
        names = [s.get("name") for s in (pod["spec"].get("imagePullSecrets") or [])]
        if secret_name not in names:
            continue
        refs = pod["metadata"].get("ownerReferences") or []
        owners.add(refs[0]["name"] if refs else pod["metadata"]["name"])
    return sorted(owners)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    parser.add_argument("-n", "--namespace", action="append", default=[], help="limit to a namespace (repeatable)")
    parser.add_argument("--old-host", default=OLD_HOST)
    parser.add_argument("--new-host", default=NEW_HOST)
    parser.add_argument(
        "--replace-user",
        default=None,
        help="rewrite secrets whose username is this, using ROTATE_USERNAME/ROTATE_PASSWORD",
    )
    parser.add_argument("--backup-dir", default=None, help="where to write pre-change copies")
    parser.add_argument("--skip-probe", action="store_true", help="do not verify credentials first (not advised)")
    args = parser.parse_args(argv)

    replacement = None
    if args.replace_user:
        user = os.environ.get("ROTATE_USERNAME")
        password = os.environ.get("ROTATE_PASSWORD")
        if not user or not password:
            parser.error("--replace-user needs ROTATE_USERNAME and ROTATE_PASSWORD in the environment")
        replacement = (user, password)

    print("Registry rotation: %s -> %s" % (args.old_host, args.new_host))
    print("Mode: %s\n" % ("APPLY" if args.apply else "dry run (use --apply to write)"))

    secrets = load_pull_secrets(args.namespace)
    sealed = sealed_owned(args.namespace)

    todo, done, sealed_hits, no_old = [], [], [], []
    for s in secrets:
        auths = (s["config"] or {}).get("auths") or {}
        # Done is decided by the NEW host being present, never by the old one being
        # absent. rekey() keeps the old entry on purpose, so "still carries the old
        # host" is true of every secret this has ever rotated. Classifying on that
        # reported finished work as outstanding forever and never once printed
        # "already on". The write stayed idempotent, so the run was harmless and only
        # the output was wrong -- which is the worse half of the two, because it left
        # no way to confirm from the script that the rotation had landed.
        if args.new_host in auths:
            done.append(s)
            continue
        if args.old_host not in auths:
            no_old.append(s)
            continue
        if (s["namespace"], s["name"]) in sealed:
            sealed_hits.append(s)
            continue
        todo.append(s)

    print("%s pull secret(s) found" % len(secrets))
    print("  %-3s already on %s" % (len(done), args.new_host))
    print("  %-3s on neither host (left alone)" % len(no_old))
    print("  %-3s sealed — reconciled from git, not touched here" % len(sealed_hits))
    print("  %-3s to re-key\n" % len(todo))

    if not todo and not sealed_hits:
        print("Nothing to do.")
        return 0

    # Probe each distinct credential once, not once per secret: 27 secrets share
    # three robot accounts, and a probe is two network round trips per repository.
    verdicts = {}
    if todo and not args.skip_probe:
        print("Verifying credentials against %s:" % args.new_host)
        for s in todo:
            entry = s["config"]["auths"][args.old_host]
            user = replacement[0] if (replacement and entry.get("username") == args.replace_user) else entry.get("username")
            password = replacement[1] if (replacement and entry.get("username") == args.replace_user) else entry.get("password")
            if user in verdicts:
                continue
            ok, detail = probe_credential(user, password, args.new_host)
            verdicts[user] = (ok, detail)
            print("  %-20s %s  (%s)" % (user, "OK" if ok else "CANNOT PULL", detail))
        print()

    writable, blocked = [], []
    for s in todo:
        user = s["config"]["auths"][args.old_host].get("username")
        effective = replacement[0] if (replacement and user == args.replace_user) else user
        if args.skip_probe or verdicts.get(effective, (True, ""))[0]:
            writable.append(s)
        else:
            blocked.append(s)

    if blocked:
        print("SKIPPING %s secret(s) whose credential cannot pull from %s:" % (len(blocked), args.new_host))
        for s in blocked:
            print("  %-20s %-22s user=%s" % (s["namespace"], s["name"], s["config"]["auths"][args.old_host].get("username")))
        print("  Recreate that robot in Harbor, then re-run with:")
        print("    ROTATE_USERNAME=... ROTATE_PASSWORD=... %s --apply --replace-user '<user>'\n" % sys.argv[0])

    if sealed_hits:
        print("SEALED — regenerate these from git instead of applying directly:")
        for s in sealed_hits:
            print("  %-20s %-22s" % (s["namespace"], s["name"]))
        print("    kubectl create secret docker-registry <name> \\")
        print("        --docker-server='%s' --docker-username=... --docker-password=... \\" % args.new_host)
        print("        -n <namespace> --dry-run=client -o yaml \\")
        print("      | kubeseal -o yaml > cluster/<path>/sealed-secret-<name>.yaml")
        print("    then commit to colfax-ops and let ArgoCD sync it.\n")

    if not writable:
        print("No secret can be written.")
        return 1 if blocked else 0

    print("Re-keying %s secret(s):" % len(writable))
    for s in writable:
        print("  %-20s %-22s" % (s["namespace"], s["name"]), end="")
        users = workloads_using(s["namespace"], s["name"])
        print("  used by: %s" % (", ".join(users) if users else "no running pods"))

    if not args.apply:
        print("\nDry run — nothing written. Re-run with --apply.")
        return 0

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    directory = args.backup_dir or os.path.join(os.path.expanduser("~"), ".registry-rotation-backup", stamp)
    backup(writable, directory)
    print("\nBacked up %s secret(s) to %s" % (len(writable), directory))

    failures = 0
    for s in writable:
        entry_user = s["config"]["auths"][args.old_host].get("username")
        use = replacement if (replacement and entry_user == args.replace_user) else None
        result = rekey(s["config"], args.old_host, args.new_host, replacement=use)
        if not result:
            continue
        new_config, _ = result
        encoded = base64.b64encode(json.dumps(new_config).encode()).decode()
        patch = json.dumps({"data": {CONFIG_KEY: encoded}})
        try:
            kubectl("patch", "secret", s["name"], "-n", s["namespace"], "--type", "merge", "-p", patch)
            print("  patched %s/%s" % (s["namespace"], s["name"]))
        except RuntimeError as exc:
            print("  FAILED  %s/%s: %s" % (s["namespace"], s["name"], exc))
            failures += 1

    print("\nDone. %s patched, %s failed." % (len(writable) - failures, failures))
    print("Nothing was restarted. Running pods keep their image; the new credential")
    print("is read at the next pull. Restart the workloads listed above when ready.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
