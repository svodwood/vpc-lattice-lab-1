from urllib.request import urlopen
import os

green_endpoint = os.environ.get("GREEN_ENDPOINT")

def lambda_handler(event, context):
    response = urlopen(green_endpoint).read()
    print(response)