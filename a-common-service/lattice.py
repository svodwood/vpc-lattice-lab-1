from pulumi_aws_native import vpclattice
from pulumi_aws import ram
from pulumi import ResourceOptions, export

from settings import baseline_cost_tags, deployment_region, baseline_cost_tags_native, green_principal, blue_principal
from vpc import green_network_vpc, blue_network_vpc, green_lattice_sg, blue_lattice_sg

"""
Creates the RAM shares for Lattice service networks:
"""
green_ram_share = ram.ResourceShare("GreenLatticeRamShare",
    allow_external_principals=False, # Make note that this share will not work outside your AWS Organization by default, set to True if needed
    tags=baseline_cost_tags
)

blue_ram_share = ram.ResourceShare("BlueLatticeRamShare",
    allow_external_principals=False, # Make note that this share will not work outside your AWS Organization by default, set to True if needed
    tags=baseline_cost_tags
)

"""
Associates principals to the RAM shares:
"""
green_principal_association = ram.PrincipalAssociation("GreenPrincipalAssociation",
    principal=green_principal,
    resource_share_arn=green_ram_share.arn
)

blue_principal_association = ram.PrincipalAssociation("BluePrincipalAssociation",
    principal=blue_principal,
    resource_share_arn=blue_ram_share.arn
)

"""
Constructs green and blue service networks:
"""
green_service_network = vpclattice.ServiceNetwork("GreenServiceNetwork",
    auth_type="NONE",
    name="green-service-network",
    tags=baseline_cost_tags_native
)

export("green-service-network-arn", green_service_network.arn)

blue_service_network = vpclattice.ServiceNetwork("BlueServiceNetwork",
    auth_type="NONE",
    name="blue-service-network",
    tags=baseline_cost_tags_native
)

export("blue-service-network-arn", blue_service_network.arn)

"""
Adds service networks to respective RAM shares:
"""
green_ram_share_association = ram.ResourceAssociation("GreenLatticeRamShareAssociation",
    resource_arn=green_service_network.arn,
    resource_share_arn=green_ram_share.arn,
    opts=ResourceOptions(
        parent=green_ram_share,
        depends_on=[
            green_service_network
        ]
    )
)

blue_ram_share_association = ram.ResourceAssociation("BlueLatticeRamShareAssociation",
    resource_arn=blue_service_network.arn,
    resource_share_arn=blue_ram_share.arn,
    opts=ResourceOptions(
        parent=blue_ram_share,
        depends_on=[
            blue_service_network
        ]
    )
)

"""
Adds service netowork VPC associations (Green Peer and Blue Peer in SharedServices):
"""
green_service_network_vpc_association = vpclattice.ServiceNetworkVpcAssociation("GreenServiceNetworkVpcAssociation",
    security_group_ids=[green_lattice_sg.id],
    service_network_identifier=green_service_network,
    vpc_identifier=green_network_vpc,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        parent=green_service_network,
        depends_on=[
            green_service_network,
            green_network_vpc
        ]
    )
)

blue_service_network_vpc_association = vpclattice.ServiceNetworkVpcAssociation("BlueServiceNetworkVpcAssociation",
    security_group_ids=[blue_lattice_sg.id],
    service_network_identifier=blue_service_network,
    vpc_identifier=blue_network_vpc,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        parent=blue_service_network,
        depends_on=[
            blue_service_network,
            blue_network_vpc
        ]
    )
)