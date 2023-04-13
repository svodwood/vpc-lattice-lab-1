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
stack_config = Config()
provider_config = Config("aws")
deployment_region = provider_config.require("region")

baseline_cost_tags = {
    "Account": "GreenSandbox",
    "AccountType": "Workload",
    "Provisioned": "Pulumi",
    "StackName": "green-service"
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

green_sandbox_vpc_cidr = "10.200.0.0/16"

green_lattice_network_arn = stack_config.require("lattice-network-arn")

green_sandbox_subnet_cidrs_pub = [
    "10.200.0.0/18",
    "10.200.64.0/18"
]

green_sandbox_subnet_cidrs_app = [
    "10.200.128.0/18",
    "10.200.192.0/18"
]

shared_service_fqdn = stack_config.require("shared-service-fqdn")