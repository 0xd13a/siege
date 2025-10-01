variable "azure_subscription_id" {
  type = string
}

variable "env" {
  type = string
}

variable "location" {
  type = string
}

variable "admin_ssh_key_path" {
  type = string
}

variable "player_password" {
  default = null
  type = string
}

variable "admin_username" {
  type = string
}

variable "services_list" {
  type = string
  default = "services.yaml"
}

variable "teams_list" {
  type = string
  default = "teams.yaml"
}


variable "home_folder" {
  type = string
  default = "teams.yaml"
}