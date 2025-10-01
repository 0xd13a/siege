# Provisioning the infrastructure 

This folder contains scripts that provision competition infrastructure in the cloud.

We currently support provisioning in Azure only, support for other cloud environments will be added in the future. Before proceeding make sure that you authenticate to Azure as a user with sufficient rights:

```
az login --scope https://graph.microsoft.com/.default
```

Instructions are provided for provisioning from a Linux environment, but they should be applicable, with minimal changes, to other OSes.

## To provision an example Siege competition

* Edit `siege/example_competition/siege/settings.tfvars` and set values to match your requirements

* On command line, go to folder `siege/infra/terraform/azure/competition`

* Execute the following command to verify that the provisioned environment does not have problems:

```
terraform plan -var-file=../../../../example_competition/siege/settings.tfvars
```

* If that worked successfully, you are ready to provision the infrastructure. To do that, in the previous command replace `plan` with `apply`. To destroy the environment replace `apply` with `destroy`.

* The cloud resources should now be created, and the inventory and team OpenVPN files should be available in `siege/example_competition/siege/inventory`

* *(WORK IN PROGRESS) Here we will provide instructions on how to set up provisioned boxes and start the competition*

## To provision an example Siege Light competition

* Edit `siege/example_competition/siege-light/settings.tfvars` and set values to match your requirements

* On command line, go to folder `siege/infra/terraform/azure/light-competition`

* Execute the following command to verify that the provisioned environment does not have problems:

```
terraform plan -var-file=../../../../example_competition/siege-light/settings.tfvars
```

* If that worked successfully, you are ready to provision the infrastructure. To do that, in the previous command replace `plan` with `apply`. To destroy the environment replace `apply` with `destroy`.

* The cloud resources should now be created, and the inventory and team OpenVPN files should be available in `siege/example_competition/siege-light/inventory`

* *(WORK IN PROGRESS) Here we will provide instructions on how to set up provisioned boxes and start the competition*