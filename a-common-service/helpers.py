from pulumi_aws import get_caller_identity, get_availability_zones

"""
Various stack helper functions and configuration variables.
"""

current_account = get_caller_identity()
current_account_id = current_account.account_id
demo_azs = get_availability_zones(state="available").names