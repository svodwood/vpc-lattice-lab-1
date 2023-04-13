from pulumi import Config

"""
Various stack settings.
Below baseline tags must be applied to all created resources without exception:
1.  Key: "Account"
    Values: ["Management", "GreenSandbox", "BlueSandbox", "SharedServices"]
2.  Key: "AccountType"
    Values: ["Management", "Workload"]
3.  Key: "Provisioned"
    Values: ["Manually", "Pulumi", "Terraform", "Other"]
4.  Key: "StackName"
    Values: ["<project-name-here>"]
"""
pulumi_config = Config()
provider_config = Config("aws")
deployment_region = provider_config.require("region")

baseline_cost_tags = {
    "Account": "SharedServices",
    "AccountType": "Workload",
    "Provisioned": "Pulumi",
    "StackName": "common-service"
}

baseline_cost_tags_native = [
    {
        "key": "AccountType",
        "value": "Workload"
    },
    {
        "key": "Account",
        "value": "SharedServices"
    },
    {
        "key": "Provisioned",
        "value": "Pulumi"
    },
    {
        "key": "StackName",
        "value": "common-service"
    }
]

shared_services_main_vpc_cidr = "10.0.0.0/16"

shared_service_subnet_cidrs_pub = [
    "10.0.0.0/22",
    "10.0.4.0/22"
]

shared_service_subnet_cidrs_app = [
    "10.0.8.0/22",
    "10.0.12.0/22"
]

"""
VPC Lattice Local Peers
"""
blue_network_vpc_cidr = "192.168.0.0/23"
blue_subnet_cidrs = [ 
    "192.168.0.0/24",
    "192.168.1.0/24"	
]

green_network_vpc_cidr = "192.168.2.0/23"
green_subnet_cidrs = [ 
    "192.168.2.0/24",
    "192.168.3.0/24"	
]

"""
VPC Lattice Dev Accounts
"""
green_principal = pulumi_config.require("green-principal")
blue_principal = pulumi_config.require("blue-principal")