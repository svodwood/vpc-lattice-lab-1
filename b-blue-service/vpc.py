from pulumi_aws import ec2
from pulumi_aws_native import vpclattice
from pulumi import ResourceOptions

from settings import baseline_cost_tags, baseline_cost_tags_native, deployment_region, blue_sandbox_vpc_cidr, blue_sandbox_subnet_cidrs_pub, blue_sandbox_subnet_cidrs_app, blue_lattice_network_arn
from helpers import demo_azs

"""
Constructs Blue Sandbox VPC
"""
blue_sandbox_vpc = ec2.Vpc("BlueSandboxVpc",
    cidr_block=blue_sandbox_vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**baseline_cost_tags, "Name": f"BlueSandboxVpc-{deployment_region}"}
)

blue_sandbox_igw = ec2.InternetGateway("BlueSandboxIgw",
    vpc_id=blue_sandbox_vpc.id,
    tags={**baseline_cost_tags, "Name": f"BlueSandboxIgw-{deployment_region}"},
    opts=ResourceOptions(parent=blue_sandbox_vpc)
)

"""
Constructs Blue Services VPC's subnets:
"""
blue_sandbox_pub_subnets = []
blue_sandbox_app_subnets = []

for i in range(2):
    prefix = f"{demo_azs[i]}"

    blue_sandbox_subnet_pub = ec2.Subnet(f"BlueSandboxSubnetPub-{prefix}",
        vpc_id=blue_sandbox_vpc.id,
        cidr_block=blue_sandbox_subnet_cidrs_pub[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"BlueSandboxSubnetPub-{prefix}"},
        opts=ResourceOptions(parent=blue_sandbox_vpc)
    )

    blue_sandbox_pub_subnets.append(blue_sandbox_subnet_pub)

    blue_sandbox_rt_pub = ec2.RouteTable(f"BlueSandboxRtPub-{prefix}",
        vpc_id=blue_sandbox_vpc.id,
        tags={**baseline_cost_tags, "Name": f"BlueSandboxRtPub-{prefix}"},
        opts=ResourceOptions(parent=blue_sandbox_subnet_pub)
    )

    blue_sandbox_rt_pub_association = ec2.RouteTableAssociation(f"BlueSandboxRtaPub-{prefix}",
        route_table_id=blue_sandbox_rt_pub.id,
        subnet_id=blue_sandbox_subnet_pub.id,
        opts=ResourceOptions(parent=blue_sandbox_subnet_pub)
    )

    blue_sandbox_pub_route_to_wan = ec2.Route(f"WanPubRoute-{prefix}",
        route_table_id=blue_sandbox_rt_pub.id,
        gateway_id=blue_sandbox_igw.id,
        destination_cidr_block="0.0.0.0/0",
        opts=ResourceOptions(
            parent=blue_sandbox_rt_pub
        )
    )

    blue_sandbox_subnet_app = ec2.Subnet(f"BlueSandboxSubnetApp-{prefix}",
        vpc_id=blue_sandbox_vpc.id,
        cidr_block=blue_sandbox_subnet_cidrs_app[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"BlueSandboxSubnetApp-{prefix}"},
        opts=ResourceOptions(parent=blue_sandbox_vpc)
    )

    blue_sandbox_app_subnets.append(blue_sandbox_subnet_app)

    blue_sandbox_rt_app = ec2.RouteTable(f"BlueSandboxRtApp-{prefix}",
        vpc_id=blue_sandbox_vpc.id,
        tags={**baseline_cost_tags, "Name": f"BlueSandboxRtApp-{prefix}"},
        opts=ResourceOptions(parent=blue_sandbox_subnet_app)
    )

    blue_sandbox_rt_app_association = ec2.RouteTableAssociation(f"BlueSandboxAppRta-{prefix}",
        route_table_id=blue_sandbox_rt_app.id,
        subnet_id=blue_sandbox_subnet_app.id,
        opts=ResourceOptions(parent=blue_sandbox_subnet_app)
    )

"""
Creates Lattice Network association:
"""
blue_lattice_sg = ec2.SecurityGroup("BlueSecurityGroup",
    description="Blue Lattice Security Group",
    vpc_id=blue_sandbox_vpc.id,
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
    opts=ResourceOptions(parent=blue_sandbox_vpc)
)

blue_service_network_vpc_association = vpclattice.ServiceNetworkVpcAssociation("BlueServiceNetworkVpcAssociation",
    security_group_ids=[blue_lattice_sg.id],
    service_network_identifier=blue_lattice_network_arn,
    vpc_identifier=blue_sandbox_vpc,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        depends_on=[
            blue_sandbox_vpc
        ]
    )
)