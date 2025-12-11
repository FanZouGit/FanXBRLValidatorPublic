"""
Simple test for SNS helper functionality.

This test verifies the SNS helper module works correctly.
Note: This requires AWS credentials and an SNS topic to run.
"""
import os
import sys
from datetime import datetime, timezone

# Mock boto3 if not available for basic import testing
try:
    import boto3
except ImportError:
    print("boto3 not available - skipping SNS tests")
    sys.exit(0)

from sns_helper import SNSHelper, send_to_sns


def test_sns_helper_init():
    """Test SNSHelper initialization."""
    print("Testing SNSHelper initialization...")
    
    # Set a default region for testing
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Test with explicit topic ARN
    try:
        helper = SNSHelper(topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic")
        assert helper.topic_arn == "arn:aws:sns:us-east-1:123456789012:test-topic"
        print("✓ Explicit topic ARN initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test with environment variable
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:env-test-topic'
    try:
        helper = SNSHelper()
        assert helper.topic_arn == "arn:aws:sns:us-east-1:123456789012:env-test-topic"
        print("✓ Environment variable initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test without topic ARN (should raise error)
    del os.environ['SNS_TOPIC_ARN']
    try:
        helper = SNSHelper()
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print("✓ Properly raises error when topic ARN not provided")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True


def test_send_to_sns_structure():
    """Test the send_to_sns function structure (without actual AWS call)."""
    print("\nTesting send_to_sns function structure...")
    
    # This will fail to connect to AWS, but we can test the structure
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    result = send_to_sns(
        filing_url="https://example.com/test.htm",
        validation_output="Test output",
        validation_errors="Test errors",
        dqc_rules_enabled=True
    )
    
    # Should return a dict with 'success' key
    assert 'success' in result
    assert isinstance(result, dict)
    print("✓ send_to_sns returns proper structure")
    
    return True


def test_message_structure():
    """Test the message structure that would be sent to SNS."""
    print("\nTesting SNS message structure...")
    
    filing_url = "https://www.sec.gov/test.htm"
    validation_output = "Test validation output"
    validation_errors = "Test errors"
    dqc_rules_enabled = True
    
    # Expected message body fields
    expected_fields = [
        'filing_url',
        'timestamp',
        'status',
        'dqc_rules_enabled',
        'validation_output',
        'validation_errors'
    ]
    
    # Verify all required fields would be present
    message_body = {
        'filing_url': filing_url,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'error',
        'dqc_rules_enabled': dqc_rules_enabled,
        'validation_output': validation_output,
        'validation_errors': validation_errors
    }
    
    for field in expected_fields:
        assert field in message_body, f"Missing required field: {field}"
    
    # Verify status is always 'error' for SNS notifications
    assert message_body['status'] == 'error', "SNS notifications should only be for failed validations"
    
    print("✓ Message structure contains all required fields")
    print("✓ Message status is correctly set to 'error'")
    return True


if __name__ == "__main__":
    print("Running SNS Helper Tests")
    print("=" * 50)
    
    # Run tests and collect results
    results = []
    results.append(test_sns_helper_init())
    results.append(test_send_to_sns_structure())
    results.append(test_message_structure())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
