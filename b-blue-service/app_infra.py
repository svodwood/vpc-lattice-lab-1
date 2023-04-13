from pulumi import ResourceOptions, FileArchive, AssetArchive
from pulumi_aws import lb, iam, lambda_, ec2
import json

from settings import baseline_cost_tags, deployment_region, shared_service_fqdn
from vpc import blue_sandbox_vpc, blue_sandbox_app_subnets

"""
Lambda security group
"""

blue_lambda_func_sg = ec2.SecurityGroup("BlueLambdaFuncSecurityGroup",
    description="Lambda Security Group",
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
    tags={**baseline_cost_tags, "Name": f"BlueLambdaFuncSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=blue_sandbox_vpc)
)

"""
Constructs a Lambda IAM role
"""
blue_lambda_execution_role = iam.Role("BlueLambdaExecutionRole",
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
    tags={**baseline_cost_tags, "Name": "BlueLambdaExecutionRole"}
)

lambda_vpc_managed_policy = iam.get_policy(name="AWSLambdaVPCAccessExecutionRole")

blue_lambda_execution_role_policy_attachment = iam.RolePolicyAttachment("BlueLambdaRolePolicyAttachment",
    policy_arn=lambda_vpc_managed_policy.arn,
    role=blue_lambda_execution_role
)

"""
Constructs the Blue Lambda function:
"""
blue_function = lambda_.Function("BlueFunction",
    tags={**baseline_cost_tags, "Name": "BlueFunction"},
    role=blue_lambda_execution_role.arn,
    vpc_config=lambda_.FunctionVpcConfigArgs(
        security_group_ids=[blue_lambda_func_sg.id],
        subnet_ids=[s.id for s in blue_sandbox_app_subnets]
    ),
    replace_security_groups_on_destroy=True,
    name="BlueFunction",
    runtime="python3.8",
    code=AssetArchive(
        {
            ".": FileArchive("./blue_app"),
        }
    ),
    handler="main.lambda_handler",
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "BLUE_ENDPOINT": f"http://{shared_service_fqdn}/?q=blue"
        }
    )
)