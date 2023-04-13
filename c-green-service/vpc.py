from pulumi_aws import ec2
from pulumi_aws_native import vpclattice
from pulumi import ResourceOptions

from settings import baseline_cost_tags, baseline_cost_tags_native, deployment_region, green_sandbox_vpc_cidr, green_sandbox_subnet_cidrs_pub, green_sandbox_subnet_cidrs_app, green_lattice_network_arn
from helpers import demo_azs

"""
Constructs Green Sandbox VPC
"""
green_sandbox_vpc = ec2.Vpc("GreenSandboxVpc",
    cidr_block=green_sandbox_vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**baseline_cost_tags, "Name": f"GreenSandboxVpc-{deployment_region}"}
)

green_sandbox_igw = ec2.InternetGateway("GreenSandboxIgw",
    vpc_id=green_sandbox_vpc.id,
    tags={**baseline_cost_tags, "Name": f"GreenSandboxIgw-{deployment_region}"},
    opts=ResourceOptions(parent=green_sandbox_vpc)
)

"""
Constructs Green Services VPC's subnets:
"""
green_sandbox_pub_subnets = []
green_sandbox_app_subnets = []

for i in range(2):
    prefix = f"{demo_azs[i]}"

    green_sandbox_subnet_pub = ec2.Subnet(f"GreenSandboxSubnetPub-{prefix}",
        vpc_id=green_sandbox_vpc.id,
        cidr_block=green_sandbox_subnet_cidrs_pub[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"GreenSandboxSubnetPub-{prefix}"},
        opts=ResourceOptions(parent=green_sandbox_vpc)
    )

    green_sandbox_pub_subnets.append(green_sandbox_subnet_pub)

    green_sandbox_rt_pub = ec2.RouteTable(f"GreenSandboxRtPub-{prefix}",
        vpc_id=green_sandbox_vpc.id,
        tags={**baseline_cost_tags, "Name": f"GreenSandboxRtPub-{prefix}"},
        opts=ResourceOptions(parent=green_sandbox_subnet_pub)
    )

    green_sandbox_rt_pub_association = ec2.RouteTableAssociation(f"GreenSandboxRtaPub-{prefix}",
        route_table_id=green_sandbox_rt_pub.id,
        subnet_id=green_sandbox_subnet_pub.id,
        opts=ResourceOptions(parent=green_sandbox_subnet_pub)
    )

    green_sandbox_pub_route_to_wan = ec2.Route(f"WanPubRoute-{prefix}",
        route_table_id=green_sandbox_rt_pub.id,
        gateway_id=green_sandbox_igw.id,
        destination_cidr_block="0.0.0.0/0",
        opts=ResourceOptions(
            parent=green_sandbox_rt_pub
        )
    )

    green_sandbox_subnet_app = ec2.Subnet(f"GreenSandboxSubnetApp-{prefix}",
        vpc_id=green_sandbox_vpc.id,
        cidr_block=green_sandbox_subnet_cidrs_app[i],
        availability_zone=demo_azs[i],
        tags={**baseline_cost_tags, "Name": f"GreenSandboxSubnetApp-{prefix}"},
        opts=ResourceOptions(parent=green_sandbox_vpc)
    )

    green_sandbox_app_subnets.append(green_sandbox_subnet_app)

    green_sandbox_rt_app = ec2.RouteTable(f"GreenSandboxRtApp-{prefix}",
        vpc_id=green_sandbox_vpc.id,
        tags={**baseline_cost_tags, "Name": f"GreenSandboxRtApp-{prefix}"},
        opts=ResourceOptions(parent=green_sandbox_subnet_app)
    )

    green_sandbox_rt_app_association = ec2.RouteTableAssociation(f"GreenSandboxAppRta-{prefix}",
        route_table_id=green_sandbox_rt_app.id,
        subnet_id=green_sandbox_subnet_app.id,
        opts=ResourceOptions(parent=green_sandbox_subnet_app)
    )

"""
Creates Lattice Network association:
"""
green_lattice_sg = ec2.SecurityGroup("GreenSecurityGroup",
    description="Green Lattice Security Group",
    vpc_id=green_sandbox_vpc.id,
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
    opts=ResourceOptions(parent=green_sandbox_vpc)
)

green_service_network_vpc_association = vpclattice.ServiceNetworkVpcAssociation("GreenServiceNetworkVpcAssociation",
    security_group_ids=[green_lattice_sg.id],
    service_network_identifier=green_lattice_network_arn,
    vpc_identifier=green_sandbox_vpc,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        depends_on=[
            green_sandbox_vpc
        ]
    )
)