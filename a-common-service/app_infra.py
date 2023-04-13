from pulumi import ResourceOptions, FileArchive, AssetArchive, export
from pulumi_aws import lb, iam, lambda_, ec2
from pulumi_aws_native import vpclattice
import json

from settings import baseline_cost_tags, deployment_region, baseline_cost_tags_native, blue_principal, green_principal
from helpers import current_account_id
from vpc import main_lambda_alb_sg, shared_services_app_subnets, shared_services_main_vpc
from lattice import green_service_network, blue_service_network

"""
Constructs a private Application Load Balancer for the Lambda function:
"""
# This one costs money:
shared_service_alb = lb.LoadBalancer("DirectoryServiceLb",
    internal=True,
    load_balancer_type="application",
    security_groups=[main_lambda_alb_sg.id],
    subnets=shared_services_app_subnets,
    enable_deletion_protection=False,
    tags={**baseline_cost_tags, "Name": "DirectoryServiceLb"}
)

shared_service_target_group = lb.TargetGroup("DirectoryServiceTg",
    target_type="lambda",
    tags={**baseline_cost_tags, "Name": "DirectoryServiceTg"}
)

# This one costs money (via ALB dependency):
shared_service_listener = lb.Listener("DirectoryServiceListener",
    load_balancer_arn=shared_service_alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=shared_service_target_group.arn,
    )]
)

"""
Creates a Lambda security group in the main VPC:
"""
main_lambda_func_sg = ec2.SecurityGroup("MainLambdaFuncSecurityGroup",
    description="Lambda Security Group",
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
    tags={**baseline_cost_tags, "Name": f"MainLambdaFuncSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=shared_services_main_vpc)
)


"""
Constructs a Lambda IAM role
"""
directory_service_execution_role = iam.Role("DirectoryServiceExecutionRole",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Sid": "",
            "Principal": {
                "Service": "lambda.amazonaws.com",
            },
        }],
    }),
    tags={**baseline_cost_tags, "Name": "DirectoryServiceExecutionRole"}
)

lambda_vpc_managed_policy = iam.get_policy(name="AWSLambdaVPCAccessExecutionRole")

directory_service_execution_role_policy_attachment = iam.RolePolicyAttachment("DirectoryServiceExecutionRolePolicyAttachment",
    policy_arn=lambda_vpc_managed_policy.arn,
    role=directory_service_execution_role
)

"""
Creates the DirectoryService Lambda layer:
"""

layer_asset = FileArchive("./directory_app_layer/lambda_layer.zip")

service_layer = lambda_.LayerVersion("DirectoryServiceLayer",
    compatible_runtimes=["python3.8"],
    code=layer_asset,
    layer_name="lambda_layer"
)

"""
Constructs the DirectoryService Lambda function:
"""
service_function = lambda_.Function("DirectoryServiceFunction",
    tags={**baseline_cost_tags, "Name": "DirectoryServiceFunction"},
    role=directory_service_execution_role.arn,
    vpc_config=lambda_.FunctionVpcConfigArgs(
        security_group_ids=[main_lambda_func_sg.id],
        subnet_ids=[s.id for s in shared_services_app_subnets]
    ),
    replace_security_groups_on_destroy=True,
    name="DirectoryServiceFunction",
    runtime="python3.8",
    layers=[service_layer],
    code=AssetArchive(
        {
            ".": FileArchive("./directory_app"),
        }
    ),
    handler="main.lambda_handler"
)

"""
Adds the ALB Lambda invoke permission:
"""
alb_invoke_permission = lambda_.Permission("AlbFunctionPermission",
    action="lambda:InvokeFunction",
    function=service_function.name,
    principal="elasticloadbalancing.amazonaws.com",
    source_arn=shared_service_target_group.arn
)

"""
Attaches the Lambda function to the target group:
"""
service_function_target_group_attachment = lb.TargetGroupAttachment("FunctionTargetGroupAttachment",
    target_group_arn=shared_service_target_group.arn,
    target_id=service_function.arn,
    opts=ResourceOptions(depends_on=[alb_invoke_permission]))

"""
Creates a Lattice target group:
"""
shared_service_lattice_tg = vpclattice.TargetGroup("SharedServiceTargetGroup",
    type="ALB",
    config=vpclattice.TargetGroupConfigArgs(
        port=80,
        protocol="HTTP",
        vpc_identifier=shared_services_main_vpc.id
    ),
    name="shared-service-target",
    tags=baseline_cost_tags_native,
    targets=[vpclattice.TargetGroupTargetArgs(
        id=shared_service_alb.id,
        port=80
    )]
)

"""
Creates a Lattice service and listener:
"""
# From here big money:
shared_service_lattice_service = vpclattice.Service("SharedServiceLatticeService",
    name="shared-service",
    auth_type="AWS_IAM",
    tags=baseline_cost_tags_native
)

export("shared-service-fqdn", shared_service_lattice_service.dns_entry.domain_name)

shared_service_lattice_service_listener = vpclattice.Listener("SharedServiceLatticeServiceListener",
    name="shared-service-listener",
    protocol="HTTP",
    port=80,
    service_identifier=shared_service_lattice_service,
    tags=baseline_cost_tags_native,
    default_action=vpclattice.ListenerDefaultActionArgs(
        forward=vpclattice.ListenerForwardArgs(
            target_groups=[
                vpclattice.ListenerWeightedTargetGroupArgs(
                    target_group_identifier=shared_service_lattice_tg,
                    weight=100
                )
            ]
        )
    ),
    opts=ResourceOptions(
        depends_on=[
            shared_service_lattice_service
        ]
    )
)

blue_service_lattice_service_association = vpclattice.ServiceNetworkServiceAssociation("BlueServiceLatticeServiceAssociation",
    service_identifier=shared_service_lattice_service,
    service_network_identifier=blue_service_network,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        depends_on=[
            shared_service_lattice_service
        ]
    )
)

green_service_lattice_service_association = vpclattice.ServiceNetworkServiceAssociation("GreenServiceLatticeServiceAssociation",
    service_identifier=shared_service_lattice_service,
    service_network_identifier=green_service_network,
    tags=baseline_cost_tags_native,
    opts=ResourceOptions(
        depends_on=[
            shared_service_lattice_service
        ]
    )
)

shared_service_auth_policy = vpclattice.AuthPolicy("SharedServiceAuthPolicy",
    policy={
        "Version":"2012-10-17",
        "Statement":[
            {
                "Effect":"Allow",
                "Principal": "*",
                "Action":"vpc-lattice-svcs:Invoke",
                "Resource": "*",
                "Condition":{
                    "StringEquals": {
                        "vpc-lattice-svcs:RequestMethod": "GET",
                        "vpc-lattice-svcs:RequestQueryString/q": "blue",
                        "vpc-lattice-svcs:SourceVpcOwnerAccount": f"{blue_principal}"
                    }
                }
            },
            {
                "Effect":"Allow",
                "Principal": "*",
                "Action":"vpc-lattice-svcs:Invoke",
                "Resource": "*",
                "Condition":{
                    "StringEquals": {
                        "vpc-lattice-svcs:RequestMethod": "GET",
                        "vpc-lattice-svcs:RequestQueryString/q": "green",
                        "vpc-lattice-svcs:SourceVpcOwnerAccount": f"{green_principal}"
                    }
                }
            }
        ]
    },
    resource_identifier=shared_service_lattice_service,
    opts=ResourceOptions(
        depends_on=[
            shared_service_lattice_service
        ]
    )
)