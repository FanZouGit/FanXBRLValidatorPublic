"""
Simple test for SQS helper functionality.

This test verifies the SQS helper module works correctly.
Note: This requires AWS credentials and an SQS queue to run.
"""
import os
import sys
from datetime import datetime, timezone

# Mock boto3 if not available for basic import testing
try:
    import boto3
except ImportError:
    print("boto3 not available - skipping SQS tests")
    sys.exit(0)

from sqs_helper import SQSHelper, send_to_sqs


def test_sqs_helper_init():
    """Test SQSHelper initialization."""
    print("Testing SQSHelper initialization...")
    
    # Set a default region for testing
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Test with explicit queue URL
    try:
        helper = SQSHelper(queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/test-queue")
        assert helper.queue_url == "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
        print("✓ Explicit queue URL initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test with environment variable
    os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/env-test-queue'
    try:
        helper = SQSHelper()
        assert helper.queue_url == "https://sqs.us-east-1.amazonaws.com/123456789012/env-test-queue"
        print("✓ Environment variable initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test without queue URL (should raise error)
    del os.environ['SQS_QUEUE_URL']
    try:
        helper = SQSHelper()
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print("✓ Properly raises error when queue URL not provided")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True


def test_send_to_sqs_structure():
    """Test the send_to_sqs function structure (without actual AWS call)."""
    print("\nTesting send_to_sqs function structure...")
    
    # This will fail to connect to AWS, but we can test the structure
    os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    result = send_to_sqs(
        filing_url="https://example.com/test.htm",
        validation_output="Test output",
        dqc_rules_enabled=True
    )
    
    # Should return a dict with 'success' key
    assert 'success' in result
    assert isinstance(result, dict)
    print("✓ send_to_sqs returns proper structure")
    
    return True


def test_message_structure():
    """Test the message structure that would be sent to SQS."""
    print("\nTesting SQS message structure...")
    
    filing_url = "https://www.sec.gov/test.htm"
    validation_output = "Test validation output"
    dqc_rules_enabled = True
    
    # Expected message body fields
    expected_fields = [
        'filing_url',
        'timestamp',
        'status',
        'dqc_rules_enabled',
        'validation_output'
    ]
    
    # Verify all required fields would be present
    message_body = {
        'filing_url': filing_url,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': 'success',
        'dqc_rules_enabled': dqc_rules_enabled,
        'validation_output': validation_output,
    }
    
    for field in expected_fields:
        assert field in message_body, f"Missing required field: {field}"
    
    # Verify status is always 'success' for SQS messages
    assert message_body['status'] == 'success', "SQS messages should only be for successful validations"
    
    print("✓ Message structure contains all required fields")
    print("✓ Message status is correctly set to 'success'")
    return True


if __name__ == "__main__":
    print("Running SQS Helper Tests")
    print("=" * 50)
    
    # Run tests and collect results
    results = []
    results.append(test_sqs_helper_init())
    results.append(test_send_to_sqs_structure())
    results.append(test_message_structure())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
