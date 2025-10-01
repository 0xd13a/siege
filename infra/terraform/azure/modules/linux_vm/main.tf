resource "azurerm_public_ip" "vm_public_ip" {
  count               = var.public_ip == true ? 1 : 0
  name                = "${var.env}-${var.vm_role}-public-ip"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "vm_nic" {
  name                  = "${var.env}-${var.vm_role}-nic"
  location              = var.resource_group_location
  resource_group_name   = var.resource_group_name
  ip_forwarding_enabled = var.enable_ip_forwarding

  ip_configuration {
    name                          = "${var.env}-${var.vm_role}-nic"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Static"
    private_ip_address            = var.private_ip
    public_ip_address_id          = var.public_ip == true ? azurerm_public_ip.vm_public_ip[0].id : null
  }
}

resource "azurerm_network_interface_security_group_association" "interface_security_group" {
  network_interface_id      = azurerm_network_interface.vm_nic.id
  network_security_group_id = var.security_group_id
}


resource "azurerm_linux_virtual_machine" "linux_vm" {
  name                  = "${var.env}-${var.vm_role}-vm"
  location              = var.resource_group_location
  resource_group_name   = var.resource_group_name
  network_interface_ids = [azurerm_network_interface.vm_nic.id]
  size                  = var.vm_size
  admin_username        = var.admin_username
  computer_name         = var.vm_role

  source_image_reference {
    publisher = var.storage_image_publisher
    offer     = var.storage_image_offer
    sku       = var.storage_image_sku
    version   = var.storage_version
  }

  os_disk {
    name                 = "${var.env}-${var.vm_role}-disk"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.admin_ssh_key_path)
  }

  admin_password = var.player_password
  disable_password_authentication = (
    (var.player_password == "" || var.player_password == null) ? true : false)

  identity {
    type = "SystemAssigned"
  }
}
