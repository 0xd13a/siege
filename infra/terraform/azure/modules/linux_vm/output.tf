output "vm_public_ip" {
  value = var.public_ip ? azurerm_public_ip.vm_public_ip[0].ip_address : ""
}