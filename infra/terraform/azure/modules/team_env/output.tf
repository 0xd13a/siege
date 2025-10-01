output "team_vpn_ip" {
  value = module.vpn_access_server.vpn_public_ip
}

output "team_gateway_ip" {
  value = module.vpn_access_server.gateway_public_ip
}

output "team_id" {
  value = var.team_id
}

output "service_ips" {
  value = local.service_ips
}