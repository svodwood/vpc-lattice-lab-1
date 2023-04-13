# VPC Lattice - Lab 1


Common service Lambda zipped layer (./directory_app_layer/lambda_zip_layer.zip) is created beforehand using the following steps. If you want to re-build, make sure to use Python3.8.

1. cd to ./directory_app
2. Inside "directory_app", mind the required structure for AWS Lambda: "python/lib/python3.8/site-packages"
3. Create venv with: python3.8 -m venv venv (if using venv to install dependencies)
4. ./venv/bin/pip install -r requirements.txt --target ./python/lib/python3.8/site-packages
5. zip -r9 lambda_layer.zip . -x venv/\*