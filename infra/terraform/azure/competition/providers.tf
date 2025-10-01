terraform {
  required_providers {
    azurerm = {
      source  = "azurerm"
      version = ">=4.23.0"
    }
  }

  backend "local" {
    path = "../terraform.tfstate"
  }
}

provider "azurerm" {
      features {}
      subscription_id = var.azure_subscription_id
}
