import subprocess
import json
import os

AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']

IMAGE_NAME = 'lambda-layer'
REPO_NAME = f'{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/python/tensorflow-dependencies'

def get_temporary_credentials():
    """
    Assume a temporary AWS IAM role for ECR access and set environment credentials.

    Uses AWS STS (Security Token Service) to assume a temporary role with limited
    permissions instead of using long-term access keys. This follows AWS security
    best practices and provides time-limited access to resources.

    Role Requirements:
        - ECRAccessRole must exist in the target AWS account
        - Role should have the minimum required permissions for ECR operations
        - ECRUser profile must have sts:AssumeRole permission for ECRAccessRole

    Notes:
        - Credentials are temporary and will expire after 1 hour
        - The ECRUser profile should be configured in ~/.aws/credentials or ~/.aws/config
        - Role session name 'ecrSession' is used for AWS CloudTrail logging
    """
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
    """
    Remove temporary AWS credentials from environment variables for security cleanup.

    This function removes the temporary AWS credentials that were set by get_temporary_credentials()
    to prevent credential leakage and ensure clean environment state. It's designed to be called
    in a finally block to guarantee cleanup even if errors occur during deployment.

    Usage Pattern:
        try:
            get_temporary_credentials()
            # Perform CLI operations
        finally:
            remove_temporary_credentials()  # Always cleanup
    """
    for env_variable in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
        os.environ.pop(env_variable, None)
    return


def push_container_to_aws():
    """
    Authenticate with ECR, tag the Docker image, and push it to the ECR repository.

    Prerequisites:
        - Docker daemon must be running
        - Local Docker image must exist with name specified in IMAGE_NAME
        - AWS credentials must be set in environment (via get_temporary_credentials)
        - ECR repository must exist and be accessible with current credentials
    """
    print('Pushing container to AWS...')
    login_cmd = "aws ecr get-login-password --region us-east-1 " + \
        "| docker login --username AWS --password-stdin " + \
        f"{AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
    subprocess.run(login_cmd, shell=True)
    subprocess.run(f"docker tag {IMAGE_NAME}:latest {REPO_NAME}", shell=True)
    subprocess.run(f"docker push {REPO_NAME}:latest", shell=True)
    return


def main():
    """Main execution function that coordinates the image upload process."""
    try:
        get_temporary_credentials()
        push_container_to_aws()
    finally:
        remove_temporary_credentials()
    print('Done.')


if __name__ == "__main__":
    main()

