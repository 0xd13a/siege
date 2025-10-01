resource "azurerm_public_ip" "gateway_ip" {
  name                = "${var.env}-gateway-ip"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_nat_gateway" "gateway" {
  name                = "${var.env}-nat-gateway"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
  sku_name            = "Standard"
}

resource "azurerm_subnet_nat_gateway_association" "network" {
  subnet_id      = var.subnet_id
  nat_gateway_id = azurerm_nat_gateway.gateway.id
}

resource "azurerm_nat_gateway_public_ip_association" "public_ip" {
  nat_gateway_id       = azurerm_nat_gateway.gateway.id
  public_ip_address_id = azurerm_public_ip.gateway_ip.id
}

locals {
  vpn_access_server_ip = "10.0.1.4"
}

resource "azurerm_route_table" "vpc" {
  name                          = "${var.env}-rt"
  location                      = var.resource_group_location
  resource_group_name           = var.resource_group_name
  bgp_route_propagation_enabled = false

  route {
    name                   = "vpc-to-vas"
    address_prefix         = "10.10.10.0/24"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = local.vpn_access_server_ip
  }
}

resource "azurerm_subnet_route_table_association" "vpc" {
  subnet_id      = var.subnet_id
  route_table_id = azurerm_route_table.vpc.id
}

resource "azurerm_network_security_group" "vpn_access_server" {
  name                = "${var.env}-vas-nsg"
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

  # External VPN
  security_rule {
    name                       = "VPN-1194"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "1194"
    source_address_prefixes    = ["0.0.0.0/0"]
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Allow-All-Internal"
    priority                   = 1005
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefixes    = ["10.0.0.0/16"]
    destination_address_prefix = "*"
  }
}

module "vpn_access_server" {
  source = "../linux_vm"
  # Management
  env                     = var.env
  resource_group_name     = var.resource_group_name
  resource_group_location = var.resource_group_location
  vm_role                 = "vas"
  # Remote access
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  # Network
  enable_ip_forwarding = true

  public_ip         = true
  private_ip        = local.vpn_access_server_ip
  security_group_id = azurerm_network_security_group.vpn_access_server.id
  subnet_id         = var.subnet_id
}
