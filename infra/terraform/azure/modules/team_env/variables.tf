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

variable "home_folder" {
  type = string
}

variable "services_list" {
  type = string
}

variable "team_id" {
  type = string
}