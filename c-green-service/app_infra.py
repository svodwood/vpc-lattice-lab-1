from pulumi import ResourceOptions, FileArchive, AssetArchive
from pulumi_aws import lb, iam, lambda_, ec2
import json

from settings import baseline_cost_tags, deployment_region, shared_service_fqdn
from vpc import green_sandbox_vpc, green_sandbox_app_subnets

"""
Lambda security group
"""

green_lambda_func_sg = ec2.SecurityGroup("GreenLambdaFuncSecurityGroup",
    description="Lambda Security Group",
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
    tags={**baseline_cost_tags, "Name": f"GreenLambdaFuncSecurityGroup-{deployment_region}"},
    opts=ResourceOptions(parent=green_sandbox_vpc)
)

"""
Constructs a Lambda IAM role
"""
green_lambda_execution_role = iam.Role("GreenLambdaExecutionRole",
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
    tags={**baseline_cost_tags, "Name": "GreenLambdaExecutionRole"}
)

lambda_vpc_managed_policy = iam.get_policy(name="AWSLambdaVPCAccessExecutionRole")

green_lambda_execution_role_policy_attachment = iam.RolePolicyAttachment("GreenLambdaRolePolicyAttachment",
    policy_arn=lambda_vpc_managed_policy.arn,
    role=green_lambda_execution_role
)

"""
Constructs the Green Lambda function:
"""
green_function = lambda_.Function("GreenFunction",
    tags={**baseline_cost_tags, "Name": "GreenFunction"},
    role=green_lambda_execution_role.arn,
    vpc_config=lambda_.FunctionVpcConfigArgs(
        security_group_ids=[green_lambda_func_sg.id],
        subnet_ids=[s.id for s in green_sandbox_app_subnets]
    ),
    replace_security_groups_on_destroy=True,
    name="GreenFunction",
    runtime="python3.8",
    code=AssetArchive(
        {
            ".": FileArchive("./green_app"),
        }
    ),
    handler="main.lambda_handler",
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "GREEN_ENDPOINT": f"http://{shared_service_fqdn}/?q=green"
        }
    )
)