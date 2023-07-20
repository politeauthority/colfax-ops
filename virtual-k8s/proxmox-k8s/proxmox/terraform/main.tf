resource "proxmox_vm_qemu" "control_plane" {
  count             = 1
  name              = "control-plane-${count.index}.k8s.cluster"
  target_node       = "${var.pm_node}"

  clone             = "ubuntu-2004-cloudinit-template"

  os_type           = "cloud-init"
  cores             = 4
  sockets           = "1"
  cpu               = "host"
  memory            = 10000
  scsihw            = "virtio-scsi-pci"
  bootdisk          = "scsi0"

  disk {
    size            = "20G"
    type            = "scsi"
    storage         = "colfax"
    iothread        = 1
  }

  network {
    model           = "virtio"
    bridge          = "vmbr0"
  }

  # cloud-init settings
  # adjust the ip and gateway addresses as needed
  ipconfig0         = "ip=192.168.50.6${count.index}/16,gw=192.168.50.1"
  sshkeys = file("${var.ssh_key_file}")
}

resource "proxmox_vm_qemu" "worker_nodes" {
  count             = 2
  name              = "worker-${count.index}.k8s.cluster"
  target_node       = "${var.pm_node}"

  clone             = "ubuntu-2004-cloudinit-template"

  os_type           = "cloud-init"
  cores             = 4
  sockets           = "1"
  cpu               = "host"
  memory            = 8000
  scsihw            = "virtio-scsi-pci"
  bootdisk          = "scsi0"

  disk {
    size            = "50G"
    type            = "scsi"
    storage         = "colfax"
    iothread        = 1
  }

  network {
    model           = "virtio"
    bridge          = "vmbr0"
  }

  # cloud-init settings
  # adjust the ip and gateway addresses as needed
  ipconfig0         = "ip=192.168.50.7${count.index}/16,gw=192.168.50.1"
  sshkeys = file("${var.ssh_key_file}")
}
