resource "azurerm_virtual_network" "scoreboard" {
  name                = "${var.env}-scoreboard-network"
  address_space       = ["10.0.0.0/16"]
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet" "scoreboard" {
  name                 = "${var.env}-scoreboard-subnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.scoreboard.name
  address_prefixes     = ["10.0.0.0/16"]
}

# defence scoreboard vm
resource "azurerm_network_security_group" "scoreboard_vm" {
  name                = "${var.env}-scoreboard-vm-nsg"
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

  security_rule {
    name                       = "HTTPS-443"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefixes    = ["0.0.0.0/0"]
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "HTTP-80"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefixes    = ["0.0.0.0/0"]
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "ScoreboardPort"
    priority                   = 1004
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = var.scoreboard_port
    source_address_prefixes    = ["0.0.0.0/0"]
    destination_address_prefix = "*"
  }
}

# from base os
module "scoreboard_vm" {
  source = "../linux_vm"
  # Management
  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  vm_role                 = "scoreboard"
  # Remote access
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  # Network
  public_ip         = true
  private_ip        = "10.0.1.10"
  security_group_id = azurerm_network_security_group.scoreboard_vm.id
  subnet_id         = azurerm_subnet.scoreboard.id
}
