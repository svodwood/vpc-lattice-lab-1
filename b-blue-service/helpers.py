from pulumi_aws import get_caller_identity, get_availability_zones
from pulumi_aws_native import vpclattice

from settings import blue_lattice_network_arn

"""
Various stack helper functions and configuration variables.
"""

current_account = get_caller_identity()
current_account_id = current_account.account_id
demo_azs = get_availability_zones(state="available").names