from pulumi_aws import ec2
from pulumi import ResourceOptions

from settings import baseline_cost_tags, deployment_region, shared_services_main_vpc_cidr, blue_network_vpc_cidr, green_network_vpc_cidr, blue_subnet_cidrs, green_subnet_cidrs, shared_service_subnet_cidrs_pub, shared_service_subnet_cidrs_app
from helpers import demo_azs

"""
Constructs Shared Services main VPC:
"""
shared_services_main_vpc = ec2.Vpc("SharedServicesMainVpc",
    cidr_block=shared_services_main_vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**baseline_cost_tags, "Name": f"SharedServicesMainVpc-{deployment_region}"}
)

shared_services_main_igw = ec2.InternetGateway("SharedServicesMainVpcIgw",
    vpc_id=shared_services_main_vpc.id,
    tags={**baseline_cost_tags, "Name": f"SharedServicesMainVpcIgw-{deployment_region}"},
    opts=ResourceOptions(parent=shared_services_main_vpc)
)

"""
Constructs secondary VPCs for peering and Lattice connection:
"""
green_network_vpc = ec2.Vpc("GreenNetworkVpc",
    cidr_block=green_network_vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**baseline_cost_tags, "Name": f"GreenNetworkVpc-{deployment_region}"}
)

blue_network_vpc = ec2.Vpc("BlueNetworkVpc",
    cidr_block=blue_network_vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**baseline_cost_tags, "Name": f"BlueNetworkVpc-{deployment_region}"}
)

"""
Establishes VPC peering connections:
"""
green_peering_connection = ec2.VpcPeeringConnection("GreenPeeringConnection",
    vpc_id=shared_services_main_vpc.id,
    peer_vpc_id=green_network_vpc.id,
    auto_accept=True,
    opts=ResourceOptions(
        parent=shared_services_main_vpc,
        depends_on=[
            shared_services_main_vpc,
            green_network_vpc
        ]
    )
)

green_peering_connection_options = ec2.PeeringConnectionOptions("GreenPeeringConnectionOptions",
    vpc_peering_connection_id=green_peering_connection.id,
    accepter=ec2.PeeringConnectionOptionsAccepterArgs(
        allow_remote_vpc_dns_resolution=True,
    ),
    requester=ec2.PeeringConnectionOptionsRequesterArgs(
        allow_remote_vpc_dns_resolution=True,
    ),
    opts=ResourceOptions(
        parent=green_peering_connection,
        depends_on=[
            green_peering_connection
        ]
    )
)

blue_peering_connection = ec2.VpcPeeringConnection("BluePeeringConnection",
    vpc_id=shared_services_main_vpc.id,
    peer_vpc_id=blue_network_vpc.id,
    auto_accept=True,
    opts=ResourceOptions(
        parent=shared_services_main_vpc,
        depends_on=[
            shared_services_main_vpc,
            blue_network_vpc
        ]
    )
)

blue_peering_connection_options = ec2.PeeringConnectionOptions("BluePeeringConnectionOptions",
    vpc_peering_connection_id=blue_peering_connection.id,
    accepter=ec2.PeeringConnectionOptionsAccepterArgs(
        allow_remote_vpc_dns_resolution=True,
    ),
    requester=ec2.PeeringConnectionOptionsRequesterArgs(
        allow_remote_vpc_dns_resolution=True,
    ),
    opts=ResourceOptions(
        parent=blue_peering_connection,
        depends_on=[
            blue_peering_connection
        ]
    )
)

"""
Constructs Shared Services main VPC's subnets:
"""
shared_services_pub_subnets = []
shared_services_app_subnets = []

for i in range(2):
    prefix = f"{demo_azs[i]}"

    shared_service_subnet_pub = ec2.Subnet(f"SharedServiceSubnetPub-{prefix}",
        vpc_id=shared_services_main_vpc.id,
        cidr_block=shared_service_subnet_cidrs_pub[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"SharedServiceSubnetPub-{prefix}"},
        opts=ResourceOptions(parent=shared_services_main_vpc)
    )

    shared_services_pub_subnets.append(shared_service_subnet_pub)

    shared_service_rt_pub = ec2.RouteTable(f"SharedServiceRtPub-{prefix}",
        vpc_id=shared_services_main_vpc.id,
        tags={**baseline_cost_tags, "Name": f"SharedServiceRtPub-{prefix}"},
        opts=ResourceOptions(parent=shared_service_subnet_pub)
    )

    shared_service_rt_pub_association = ec2.RouteTableAssociation(f"SharedServiceRtaPub-{prefix}",
        route_table_id=shared_service_rt_pub.id,
        subnet_id=shared_service_subnet_pub.id,
        opts=ResourceOptions(parent=shared_service_subnet_pub)
    )

    shared_service_pub_route_to_wan = ec2.Route(f"WanPubRoute-{prefix}",
        route_table_id=shared_service_rt_pub.id,
        gateway_id=shared_services_main_igw.id,
        destination_cidr_block="0.0.0.0/0",
        opts=ResourceOptions(
            parent=shared_service_rt_pub
        )
    )

    # shared_service_eip = ec2.Eip(f"NateEip-{prefix}",
    #     tags={**general_tags, "Name": f"NateIpEip-{prefix}"},
    #     opts=ResourceOptions(
    #         parent=shared_services_main_vpc
    #     )
    # )

    # shared_service_nat_gateway = ec2.NatGateway(f"NatGateway-{prefix}",
    #     allocation_id=shared_service_eip.id,
    #     subnet_id=demo_public_subnet.id,
    #     tags={**general_tags, "Name": f"NatGateway-{prefix}"},
    #     opts=ResourceOptions(
    #         depends_on=[
    #             shared_services_main_vpc,
    #             shared_service_eip
    #         ]
    #     )
    # )

    shared_service_subnet_app = ec2.Subnet(f"SharedServiceSubnetApp-{prefix}",
        vpc_id=shared_services_main_vpc.id,
        cidr_block=shared_service_subnet_cidrs_app[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"SharedServiceSubnetApp-{prefix}"},
        opts=ResourceOptions(parent=shared_services_main_vpc)
    )

    shared_services_app_subnets.append(shared_service_subnet_app)

    shared_service_rt_app = ec2.RouteTable(f"SharedServiceRtApp-{prefix}",
        vpc_id=shared_services_main_vpc.id,
        tags={**baseline_cost_tags, "Name": f"SharedServiceRtApp-{prefix}"},
        opts=ResourceOptions(parent=shared_service_subnet_app)
    )

    shared_service_rt_app_association = ec2.RouteTableAssociation(f"SharedServiceAppRta-{prefix}",
        route_table_id=shared_service_rt_app.id,
        subnet_id=shared_service_subnet_app.id,
        opts=ResourceOptions(parent=shared_service_subnet_app)
    )

    # shared_service_app_route_to_wan = ec2.Route(f"WanAppRoute-{prefix}",
    #     route_table_id=shared_service_rt_app.id,
    #     nat_gateway_id=shared_service_nat_gateway.id,
    #     destination_cidr_block="0.0.0.0/0",
    #     opts=ResourceOptions(
    #         parent=shared_service_rt_app
    #     )
    # )

    shared_service_route_to_green = ec2.Route(f"RouteToGreenPeer-{prefix}",
        route_table_id=shared_service_rt_app.id,
        vpc_peering_connection_id=green_peering_connection.id,
        destination_cidr_block=green_network_vpc_cidr,
        opts=ResourceOptions(
            parent=shared_service_rt_app,
            depends_on=[green_peering_connection]
        )
    )

    shared_service_route_to_blue = ec2.Route(f"RouteToBluePeer-{prefix}",
        route_table_id=shared_service_rt_app.id,
        vpc_peering_connection_id=blue_peering_connection.id,
        destination_cidr_block=blue_network_vpc_cidr,
        opts=ResourceOptions(
            parent=shared_service_rt_app,
            depends_on=[blue_peering_connection]
        )
    )

"""
Constructs green network peer subnets:
"""
green_peer_subnets = []

for i in range(2):
    prefix = f"{demo_azs[i]}"

    green_peer_subnet = ec2.Subnet(f"GreenPeerSubnet-{prefix}",
        vpc_id=green_network_vpc.id,
        cidr_block=green_subnet_cidrs[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"GreenPeerSubnet-{prefix}"},
        opts=ResourceOptions(parent=green_network_vpc)
    )

    green_peer_subnets.append(green_peer_subnet)
    
    green_peer_rt = ec2.RouteTable(f"GreenPeerRt-{prefix}",
        vpc_id=green_network_vpc.id,
        tags={**baseline_cost_tags, "Name": f"GreenPeerRt-{prefix}"},
        opts=ResourceOptions(parent=green_peer_subnet)
    )

    green_peer_rt_association = ec2.RouteTableAssociation(f"GreenPeerRta-{prefix}",
        route_table_id=green_peer_rt.id,
        subnet_id=green_peer_subnet.id,
        opts=ResourceOptions(parent=green_peer_subnet)
    )

    green_peer_main_route = ec2.Route(f"GreenPeerMainRoute-{prefix}",
        route_table_id=green_peer_rt.id,
        vpc_peering_connection_id=green_peering_connection.id,
        destination_cidr_block=shared_services_main_vpc_cidr,
        opts=ResourceOptions(
            parent=green_peer_rt,
            depends_on=[green_peering_connection]
        )
    )


"""
Constructs blue network peer subnets:
"""
blue_peer_subnets = []

for i in range(2):
    prefix = f"{demo_azs[i]}"

    blue_peer_subnet = ec2.Subnet(f"BluePeerSubnet-{prefix}",
        vpc_id=blue_network_vpc.id,
        cidr_block=blue_subnet_cidrs[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"BluePeerSubnet-{prefix}"},
        opts=ResourceOptions(parent=blue_network_vpc)
    )

    blue_peer_subnets.append(blue_peer_subnet)
    
    blue_peer_rt = ec2.RouteTable(f"BluePeerRt-{prefix}",
        vpc_id=blue_network_vpc.id,
        tags={**baseline_cost_tags, "Name": f"BluePeerRt-{prefix}"},
        opts=ResourceOptions(parent=blue_peer_subnet)
    )

    blue_peer_rt_association = ec2.RouteTableAssociation(f"BluePeerRta-{prefix}",
        route_table_id=blue_peer_rt.id,
        subnet_id=blue_peer_subnet.id,
        opts=ResourceOptions(parent=blue_peer_subnet)
    )

    blue_peer_main_route = ec2.Route(f"BluePeerMainRoute-{prefix}",
        route_table_id=blue_peer_rt.id,
        vpc_peering_connection_id=blue_peering_connection.id,
        destination_cidr_block=shared_services_main_vpc_cidr,
        opts=ResourceOptions(
            parent=blue_peer_rt,
            depends_on=[blue_peering_connection]
        )
    )

"""
Creates demo security groups in the Green and Blue VPCs:
"""
green_lattice_sg = ec2.SecurityGroup("GreenSecurityGroup",
    description="Green Lattice Security Group",
    vpc_id=green_network_vpc.id,
    ingress=[ec2.SecurityGroupIngressArgs(
        description="Any",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    egress=[ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    tags={**baseline_cost_tags, "Name": f"GreenSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=green_network_vpc)
)

blue_lattice_sg = ec2.SecurityGroup("BlueSecurityGroup",
    description="Blue Lattice Security Group",
    vpc_id=blue_network_vpc.id,
    ingress=[ec2.SecurityGroupIngressArgs(
        description="Any",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    egress=[ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    tags={**baseline_cost_tags, "Name": f"BlueSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=blue_network_vpc)
)

"""
Creates a demo security group in the main VPC, to be used with the Application Load Balancer:
"""
main_lambda_alb_sg = ec2.SecurityGroup("MainLambdaAlbSecurityGroup",
    description="ALB Security Group",
    vpc_id=shared_services_main_vpc.id,
    ingress=[ec2.SecurityGroupIngressArgs(
        description="Any",
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    egress=[ec2.SecurityGroupEgressArgs(
        from_port=0,
        to_port=0,
        protocol="-1",
        cidr_blocks=["0.0.0.0/0"],
        ipv6_cidr_blocks=["::/0"],
    )],
    tags={**baseline_cost_tags, "Name": f"MainLambdaAlbSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=shared_services_main_vpc)
)