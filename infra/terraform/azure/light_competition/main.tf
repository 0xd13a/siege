resource "azurerm_resource_group" "group" {
  name     = var.env
  location = var.location
}

locals {
  teams = yamldecode(file("${var.home_folder}/config/${var.teams_list}"))

  team_names = { for index, item in local.teams.teams : "${index}" => item.name }
}

module "light_team_env" {
  source = "../modules/light_team_env"

  for_each = local.team_names

  resource_group_location = azurerm_resource_group.group.location
  resource_group_name = azurerm_resource_group.group.name
  env = "${var.env}-team-${each.key}"
  team_id = each.key
  admin_username = var.admin_username
  admin_ssh_key_path   = var.admin_ssh_key_path
  player_password = var.player_password
  home_folder = var.home_folder
  services_list = var.services_list
}

resource "local_file" "hosts_file" {
  content  = yamlencode({"teams": { "hosts": { 
    for team_env in module.light_team_env: "${team_env.team_id}" => 
        { "ansible_host" : team_env.team_vpn_ip, "gateway" : team_env.team_gateway_ip,
        "services" : team_env.service_ips }}}})
  filename = "${var.home_folder}/inventory/hosts.yaml"
}