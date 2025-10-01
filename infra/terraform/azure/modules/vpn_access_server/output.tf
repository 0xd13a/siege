output "vpn_public_ip" {
  value = module.vpn_access_server.vm_public_ip
}

output "gateway_public_ip" {
  value = azurerm_public_ip.gateway_ip.ip_address
}
