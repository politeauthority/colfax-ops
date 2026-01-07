variable "pm_api_url" {
  default = "https://192.168.50.50:8006/api2/json"
}

variable "pm_node" {
  default = "hoyt"
}

variable "pm_user" {
  default = "root@pam"
}

variable "pm_password" {
  default = "cleancut"
}

variable "ssh_key_file" {
  default = "~/.ssh/id_rsa.pub"
}
