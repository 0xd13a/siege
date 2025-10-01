variable "env" {
  type = string
}

variable "vm_role" {
  type = string
}

variable "resource_group_location" {
  type = string
}
variable "resource_group_name" {
  type = string
}

# Remote Access
variable "admin_username" {
  type = string
}
variable "admin_ssh_key_path" {
  type = string
}
variable "player_password" {
  default = null
  type = string
}

# Network
variable "private_ip" {
  type = string
}
variable "public_ip" {
  type = bool
}
variable "security_group_id" {
  type = string
}
variable "subnet_id" {
  type = string
}
variable "enable_ip_forwarding" {
  type    = bool
  default = false
}

# VM Size and OS
variable "storage_image_publisher" {
  type = string
  default = "Canonical"
}
variable "storage_image_offer" {
  type = string
  default = "ubuntu-24_04-lts"
}
variable "storage_image_sku" {
  type = string
  default = "server-gen1"
}

variable "storage_version" {
  default = "latest"
  type    = string
}
variable "vm_size" {
  type = string
  default = "Standard_B2s"
}
