resource "azurerm_network_security_group" "attack_bot" {
  name                = "${var.env}-attack-bot-nsg"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name

  # External ssh
  security_rule {
    name                       = "SSH-22"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefixes    = ["0.0.0.0/0"]
    destination_address_prefix = "*"
  }
}

module "attack_bot_vm" {
  source = "../linux_vm"
  # Management
  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  vm_role                 = "attack-bot"
  # Remote access
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  # Network
  public_ip         = false
  private_ip        = "10.0.1.10"
  security_group_id = azurerm_network_security_group.attack_bot.id
  subnet_id         = var.subnet_id
}
