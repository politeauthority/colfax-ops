# resource "proxmox_vm_qemu" "control_plane" {
#   count             = 1
#   name              = "control-plane-${count.index}.k8s.cluster"
#   target_node       = "${var.pm_node}"

#   clone             = "ubuntu-2004-cloudinit-template"

#   os_type           = "cloud-init"
#   cores             = 4
#   sockets           = "1"
#   cpu               = "host"
#   memory            = 10000
#   scsihw            = "virtio-scsi-pci"
#   bootdisk          = "scsi0"

#   disk {
#     size            = "20G"
#     type            = "scsi"
#     storage         = "colfax"
#     iothread        = 1
#   }

#   network {
#     model           = "virtio"
#     bridge          = "vmbr0"
#   }

#   # cloud-init settings
#   # adjust the ip and gateway addresses as needed
#   ipconfig0         = "ip=192.168.50.6${count.index}/16,gw=192.168.50.1"
#   sshkeys = file("${var.ssh_key_file}")
# }

# resource "proxmox_vm_qemu" "worker_nodes_colfax" {
#   count             = 3
#   name              = "worker-${count.index}.k8s.cluster"
#   target_node       = "colfax"

#   clone             = "ubuntu-2004-cloudinit-template"

#   os_type           = "cloud-init"
#   cores             = 5
#   sockets           = "1"
#   cpu               = "host"
#   memory            = 18000
#   scsihw            = "virtio-scsi-pci"
#   bootdisk          = "scsi0"

#   disk {
#     size            = "100G"
#     type            = "scsi"
#     storage         = "colfax"
#     iothread        = 1
#   }

#   network {
#     model           = "virtio"
#     bridge          = "vmbr0"
#   }

#   # cloud-init settings
#   # adjust the ip and gateway addresses as needed
#   ipconfig0         = "ip=192.168.50.7${count.index}/16,gw=192.168.50.1"
#   sshkeys = file("${var.ssh_key_file}")
# }

resource "proxmox_vm_qemu" "worker_nodes_colfax" {
  count             = 1
  name              = "worker-colfax-test.k8s.cluster"
  target_node       = "colfax"

  clone             = "ubuntu-2004-cloudinit-template-2"

  os_type           = "cloud-init"
  cores             = 6
  sockets           = "1"
  cpu               = "host"
  memory            = 4000
  scsihw            = "virtio-scsi-pci"
  bootdisk          = "scsi0"

  disk {
    size            = "10G"
    type            = "disk"
    storage         = "local"
    slot            = "sata0"
    iothread        = true
  }

  network {
    model           = "virtio"
    bridge          = "vmbr0"
  }

  #  cloud-init settings
  # adjust the ip and gateway addresses as needed
  ipconfig0         = "ip=192.168.50.79/16,gw=192.168.50.1"
  sshkeys = file("${var.ssh_key_file}")
}


# resource "proxmox_vm_qemu" "worker_nodes_hoyt" {
#   count             = 1
#   name              = "worker-hoyt-0.k8s.cluster"
#   target_node       = "hoyt"

#   clone             = "ubuntu-2004-cloudinit-template"

#   os_type           = "cloud-init"
#   cores             = 6
#   sockets           = "1"
#   cpu               = "host"
#   memory            = 4000
#   scsihw            = "virtio-scsi-pci"
#   bootdisk          = "scsi0"

#   disk {
#     size            = "10G"
#     type            = "cloudinit"
#     storage         = "local"
#     slot            = "sata0"
#     iothread        = true
#   }

#   network {
#     model           = "virtio"
#     bridge          = "vmbr0"
#   }

#   # cloud-init settings
#   # adjust the ip and gateway addresses as needed
#   ipconfig0         = "ip=192.168.50.79/16,gw=192.168.50.1"
#   sshkeys = file("${var.ssh_key_file}")
# }

