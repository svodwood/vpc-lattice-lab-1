from urllib.request import urlopen
import os

blue_endpoint = os.environ.get("BLUE_ENDPOINT")

def lambda_handler(event, context):
    response = urlopen(blue_endpoint).read()
    print(response)
