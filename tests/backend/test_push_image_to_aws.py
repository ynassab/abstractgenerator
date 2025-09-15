import pytest
import json
import os
import subprocess
from unittest import mock

TEST_AWS_ACCOUNT_ID = '123456789012'
# Patch the environment variable before importing the module
with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
    from backend.lambda_function import push_image_to_aws

AWS_REGION = 'us-east-1'

TEST_KEY_ID = 'test-key-id'
TEST_SECRET_KEY = 'test-secret-key'
TEST_SESSION_TOKEN = 'test-session-token'

class TestPushImageToAws:
    """Test cases for the database management script."""

    @mock.patch('subprocess.run')
    def test_get_temporary_credentials_success(self, mock_subprocess):
        """Test successful credential assumption."""
        # Mock subprocess response
        mock_result = mock.Mock()
        mock_result.stdout = json.dumps({
            'Credentials': {
                'AccessKeyId': TEST_KEY_ID,
                'SecretAccessKey': TEST_SECRET_KEY,
                'SessionToken': TEST_SESSION_TOKEN
            }
        })
        mock_subprocess.return_value = mock_result

        # Mock environment variable
        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            push_image_to_aws.get_temporary_credentials()

            # Verify subprocess was called once with correct parameters
            mock_subprocess.assert_called_once()

            # Verify environment variables were set correctly
            assert os.environ['AWS_ACCESS_KEY_ID'] == TEST_KEY_ID
            assert os.environ['AWS_SECRET_ACCESS_KEY'] == TEST_SECRET_KEY
            assert os.environ['AWS_SESSION_TOKEN'] == TEST_SESSION_TOKEN

    @mock.patch('subprocess.run')
    def test_get_temporary_credentials_failure(self, mock_subprocess):
        """Test handling of credential assumption failure."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'aws sts assume-role')

        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            with pytest.raises(subprocess.CalledProcessError):
                push_image_to_aws.get_temporary_credentials()

    def test_remove_temporary_credentials(self):
        """Test removal of temporary credentials from environment."""
        # Set up environment variables
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'
        os.environ['AWS_SESSION_TOKEN'] = 'test-token'

        push_image_to_aws.remove_temporary_credentials()

        # Verify environment variables were removed
        assert 'AWS_ACCESS_KEY_ID' not in os.environ
        assert 'AWS_SECRET_ACCESS_KEY' not in os.environ
        assert 'AWS_SESSION_TOKEN' not in os.environ

    def test_remove_temporary_credentials_missing_vars(self):
        """Test that removing non-existent credentials doesn't cause errors."""
        # Ensure variables don't exist
        for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN']:
            os.environ.pop(var, None)

        # Should not raise an exception
        push_image_to_aws.remove_temporary_credentials()

    @mock.patch('subprocess.run')
    def test_push_container_to_aws_success(self, mock_subprocess):
        """Test successful container push to AWS."""
        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            push_image_to_aws.push_container_to_aws()

            # Verify command patterns without hardcoding exact commands
            calls = [call[0][0] for call in mock_subprocess.call_args_list]

            # Check that login command contains expected elements
            assert any('ecr get-login-password' in call and 'docker login' in call for call in calls)
            # Check that tag command contains expected elements
            assert any('docker tag' in call and 'lambda-layer:latest' in call for call in calls)
            # Check that push command contains expected elements
            assert any('docker push' in call and TEST_AWS_ACCOUNT_ID in call for call in calls)

    @mock.patch('subprocess.run')
    def test_push_container_to_aws_login_failure(self, mock_subprocess):
        """Test handling of Docker login failure."""
        # Subprocess side effect list is length 3 because subprocess.run() is called 3 times
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, 'docker login'),  # Login fails
            None,  # Won't reach subsequent calls
            None
        ]

        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            with pytest.raises(subprocess.CalledProcessError):
                push_image_to_aws.push_container_to_aws()

    @mock.patch('backend.lambda_function.push_image_to_aws.remove_temporary_credentials')
    @mock.patch('backend.lambda_function.push_image_to_aws.push_container_to_aws')
    @mock.patch('backend.lambda_function.push_image_to_aws.get_temporary_credentials')
    @mock.patch('builtins.print')
    def test_main_success(self, mock_print, mock_get_creds, mock_push, mock_remove_creds):
        """Test successful main execution flow."""
        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            push_image_to_aws.main()

            # Verify call sequence
            mock_get_creds.assert_called_once()
            mock_push.assert_called_once()
            mock_remove_creds.assert_called_once()

    @mock.patch('backend.lambda_function.push_image_to_aws.remove_temporary_credentials')
    @mock.patch('backend.lambda_function.push_image_to_aws.push_container_to_aws')
    @mock.patch('backend.lambda_function.push_image_to_aws.get_temporary_credentials')
    def test_main_cleanup_on_exception(self, mock_get_creds, mock_push, mock_remove_creds):
        """Test that cleanup occurs even when push fails."""
        mock_push.side_effect = Exception("Push failed")

        with mock.patch.dict(os.environ, {'AWS_ACCOUNT_ID': TEST_AWS_ACCOUNT_ID}):
            with pytest.raises(Exception):
                push_image_to_aws.main()

            # Verify cleanup still happened
            mock_remove_creds.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

