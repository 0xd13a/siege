resource "azurerm_network_security_group" "vulnerable_service_vm" {
  name                = "${var.env}-vuln-service-nsg"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name

  # External ssh
  security_rule {
    name                       = "All-Inbound"
    priority                   = 1010
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefixes    = ["10.0.0.0/16"]
    destination_address_prefix = "*"
  }
}

module "vulnerable_service_vm" {
  source = "../linux_vm"

  for_each = var.service_ips

  # Management
  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  vm_role                 = "vuln-service-${each.key}"
  # Remote access
  admin_username = var.admin_username
  admin_ssh_key_path = var.admin_ssh_key_path
  player_password = var.player_password

  # Network
  public_ip         = false
  private_ip        = each.value
  security_group_id = azurerm_network_security_group.vulnerable_service_vm.id
  subnet_id         = var.subnet_id
}
