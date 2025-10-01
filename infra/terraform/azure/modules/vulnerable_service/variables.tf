variable "resource_group_name" {
  type        = string
}

variable "resource_group_location" {
  type        = string
}

variable "env" {
  type = string
}

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

variable "subnet_id" {
  type = string
}

variable "service_ips" {
  type = map(string)
}