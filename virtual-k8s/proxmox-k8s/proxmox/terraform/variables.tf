variable "pm_api_url" {
  default = "https://localhost:8006/api2/json"
}

variable "pm_node" {
  default = "colfax"
}

variable "pm_user" {
  default = "root@pam"
}

variable "pm_password" {
  default = "<your-password>"
}

variable "ssh_key_file" {
  default = "~/.ssh/id_rsa.pub"
}
