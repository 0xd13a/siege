resource "azurerm_virtual_network" "main" {
  name                = "${var.env}-network"
  address_space       = ["10.0.0.0/16"]
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet" "internal" {
  name                 = "${var.env}-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/16"]
}

locals {
  services = yamldecode(file("${var.home_folder}/config/${var.services_list}"))

  service_ips = { for service in local.services.services : service.folder => split(":", service.address)[0] }
}

module "vpn_access_server" {
  source = "../vpn_access_server"

  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  subnet_id = azurerm_subnet.internal.id
}

module "attack_bot" {
  source = "../attack_bot"

  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  subnet_id = azurerm_subnet.internal.id
}


module "vulnerable_service" {
  source = "../vulnerable_service"

  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path

  player_password = var.player_password

  subnet_id = azurerm_subnet.internal.id
  service_ips = local.service_ips
}
