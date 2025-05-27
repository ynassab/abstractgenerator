import subprocess
import json
import os

AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']

IMAGE_NAME = 'lambda-layer'
REPO_NAME = f'{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/python/tensorflow-dependencies'

def get_temporary_credentials():
    cmd = "aws sts assume-role --profile ECRUser " + \
    f"--role-arn arn:aws:iam::{AWS_ACCOUNT_ID}:role/ECRAccessRole " + \
    "--role-session-name ecrSession"
    result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE)
    credentials = json.loads(result.stdout)['Credentials']
    os.environ['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']
    print('Assumed temporary user role.')
    return


def remove_temporary_credentials():
    for env_variable in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
        os.environ.pop(env_variable)
    return


def push_container_to_aws():
    print('Pushing container to AWS...')
    login_cmd = "aws ecr get-login-password --region us-east-1 " + \
        "| docker login --username AWS --password-stdin " + \
        f"{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
    subprocess.run(login_cmd, shell=True)
    subprocess.run(f"docker tag {IMAGE_NAME}:latest {REPO_NAME}", shell=True)
    subprocess.run(f"docker push {REPO_NAME}:latest", shell=True)
    return


if __name__ == "__main__":
    get_temporary_credentials()
    try:
        push_container_to_aws()
    finally:
        remove_temporary_credentials()
    print('Done.')

