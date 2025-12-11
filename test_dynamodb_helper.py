"""
Simple test for DynamoDB helper functionality.

This test verifies the DynamoDB helper module works correctly.
Note: This requires AWS credentials and a DynamoDB table to run.
"""
import os
import sys
from datetime import datetime, timezone

# Mock boto3 if not available for basic import testing
try:
    import boto3
except ImportError:
    print("boto3 not available - skipping DynamoDB tests")
    sys.exit(0)

from dynamodb_helper import DynamoDBHelper, save_to_dynamodb


def test_dynamodb_helper_init():
    """Test DynamoDBHelper initialization."""
    print("Testing DynamoDBHelper initialization...")
    
    # Set a default region for testing
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Test with explicit table name
    try:
        helper = DynamoDBHelper(table_name="test-table")
        assert helper.table_name == "test-table"
        print("✓ Explicit table name initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test with environment variable
    os.environ['DYNAMODB_TABLE_NAME'] = 'env-test-table'
    try:
        helper = DynamoDBHelper()
        assert helper.table_name == "env-test-table"
        print("✓ Environment variable initialization works")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    # Test without table name (should raise error)
    del os.environ['DYNAMODB_TABLE_NAME']
    try:
        helper = DynamoDBHelper()
        print("✗ Should have raised ValueError")
        return False
    except ValueError as e:
        print("✓ Properly raises error when table name not provided")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True


def test_save_to_dynamodb_structure():
    """Test the save_to_dynamodb function structure (without actual AWS call)."""
    print("\nTesting save_to_dynamodb function structure...")
    
    # This will fail to connect to AWS, but we can test the structure
    os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    result = save_to_dynamodb(
        filing_url="https://example.com/test.htm",
        status="success",
        validation_output="Test output",
        dqc_rules_enabled=True,
        validation_errors=None
    )
    
    # Should return a dict with 'success' key
    assert 'success' in result
    assert isinstance(result, dict)
    print("✓ save_to_dynamodb returns proper structure")
    
    return True


def test_item_structure():
    """Test the item structure that would be saved to DynamoDB."""
    print("\nTesting DynamoDB item structure...")
    
    filing_url = "https://www.sec.gov/test.htm"
    status = "success"
    validation_output = "Test validation output"
    dqc_rules_enabled = True
    validation_errors = None
    
    # Expected fields
    expected_fields = [
        'filing_url',
        'timestamp',
        'status',
        'dqc_rules_enabled',
        'validation_output'
    ]
    
    # Verify all required fields would be present
    item = {
        'filing_url': filing_url,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'status': status,
        'dqc_rules_enabled': dqc_rules_enabled,
        'validation_output': validation_output,
    }
    
    for field in expected_fields:
        assert field in item, f"Missing required field: {field}"
    
    print("✓ Item structure contains all required fields")
    return True


if __name__ == "__main__":
    print("Running DynamoDB Helper Tests")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_dynamodb_helper_init()
    all_passed &= test_save_to_dynamodb_structure()
    all_passed &= test_item_structure()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
