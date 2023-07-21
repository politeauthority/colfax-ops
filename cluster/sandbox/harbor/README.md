# Harbor

## Using in Kubernetes
Create the Docker registry secret, then use the `ImagePullSecret` of `harbor`
```bash
kubectl create secret docker-registry harbor \
    --docker-server='harbor.squid-ink.us' \
    --docker-username='user' \
    --docker-password='password' \
    --docker-email='email'
```
