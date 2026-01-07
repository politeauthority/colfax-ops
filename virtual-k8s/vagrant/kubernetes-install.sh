kubectl set env daemonset/calico-node \
	-n kube-system \
	IP_AUTODETECTION_METHOD=cidr=192.168.50.0/24
	192.168.50.60/30,192.168.50.70/32,192.168.50.71/32,192.168.50.79
kubectl set env daemonset/calico-node \
	-n kube-system \
	IP_AUTODETECTION_METHOD=can-reach=192.168.50.6


calico-node:v3.26.1



### Next Steps Taking
``````yaml
systemctl stop apparmor
systemctl disable apparmor 
systemctl restart containerd.service
```



curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg


echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt install kubeadm kubelet kubectl

sudo apt install kubeadm=1.28.2-1.1
sudo apt install kubelet=1.28.2-1.1
sudo apt install kubectl=1.28.2-1.1


