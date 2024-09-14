#!/bin/bash
# Remove all finalizers from pods.
# This is helpful for pods that are stuck in terminating, specially when github actions runners get
# into a bad state.

namespace="actions-runner-system"
delete_runners="true"

# Get a list of pod names in the specified namespace
pod_names=$(kubectl get pods -n "$namespace" --no-headers | awk '{print $1}')

# Loop through each pod and remove finalizers
for pod_name in $pod_names; do
  # Describe the pod to get its finalizers
  finalizers=$(kubectl get pod "$pod_name" -n "$namespace" -oyaml| grep "finalizers:" | awk '{print $1}')
  
  # If finalizers are found, remove them and update the pod
  if [ -n "$finalizers" ]; then
    echo "Removing finalizers for pod: $pod_name"
    kubectl patch pod "$pod_name" -n "$namespace" -p '{"metadata":{"finalizers":[]}}' --type=merge
  else
    echo "No finalizers found for pod: $pod_name"
  fi
done

if [ "$delete_runners" == "true" ]; then
runner_names=$(kubectl get runners -n "$namespace" --no-headers | awk '{print $1}')

    # Loop through each pod and remove finalizers
    for runner_name in $runner_names; do
        finalizers=$(kubectl get runner "$runner_name" -n "$namespace" -oyaml| grep "finalizers:" | awk '{print $1}')
        if [ -n "$finalizers" ]; then
            echo "Removing finalizers for runner: $runner_name"
            kubectl patch runner "$runner_name" -n "$namespace" -p '{"metadata":{"finalizers":[]}}' --type=merge
        else
            echo "No finalizers found for pod: $runner_name"
        fi
    done
fi

echo "Finalizers have been removed from all pods in namespace: $namespace"
