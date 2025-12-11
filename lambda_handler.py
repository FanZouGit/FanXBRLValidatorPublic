"""
AWS Lambda handler for XBRL filing validation.

This handler wraps the validate_filing.py functionality to make it compatible
with AWS Lambda's event-driven architecture.

Expected event structure:
{
    "filing_url": "https://www.sec.gov/path/to/filing.htm",
    "use_dqc_rules": true  // optional, defaults to true
}

Response structure:
{
    "statusCode": 200,
    "body": {
        "status": "success",
        "validation_output": "validation results...",
        "errors": []
    }
}
"""
import sys
import os
import json
import io
from contextlib import redirect_stdout, redirect_stderr

# Add Arelle to the path
arelle_path = os.path.join(os.path.dirname(__file__), 'Arelle')
if arelle_path not in sys.path:
    sys.path.insert(0, arelle_path)

from arelle import CntlrCmdLine
from dynamodb_helper import save_to_dynamodb
from sqs_helper import send_to_sqs
from sns_helper import send_to_sns


def validate_filing(filing_url, use_dqc_rules=True):
    """
    Validates an XBRL filing using Arelle.
    
    :param filing_url: The URL or file path of the filing to validate.
    :param use_dqc_rules: Whether to apply DQC validation rules (default: True).
    :return: Tuple of (success: bool, output: str, error: str)
    """
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    # Build command line arguments
    plugins = "EDGAR/render"
    
    args = [
        "--file", filing_url,
        "--plugins", plugins,
        "--httpUserAgent", "AWS Lambda XBRL Validator",
        "--validate",
        "--disclosureSystem", "efm",
        "--logLevel", "INFO",
        "--logFormat", "[%(messageCode)s] %(message)s"
    ]
    
    # Control DQC rule execution
    if not use_dqc_rules:
        args.extend(["--parameters", "dqcRuleFilter=(?!)"])
    
    # Temporarily replace sys.argv
    original_argv = sys.argv
    success = True
    
    try:
        sys.argv = ['arelleCmdLine.py'] + args
        
        # Redirect output
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            CntlrCmdLine.parseAndRun(args)
            
    except Exception as e:
        success = False
        stderr_capture.write(f"\nException occurred: {str(e)}\n")
    finally:
        sys.argv = original_argv
    
    return success, stdout_capture.getvalue(), stderr_capture.getvalue()


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    :param event: Lambda event object containing filing_url and optional use_dqc_rules
    :param context: Lambda context object
    :return: Response object with validation results
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Parse input
    try:
        if isinstance(event, str):
            event = json.loads(event)
        
        filing_url = event.get('filing_url')
        if not filing_url:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'status': 'error',
                    'message': 'Missing required parameter: filing_url'
                })
            }
        
        use_dqc_rules = event.get('use_dqc_rules', True)
        
        print(f"Validating filing: {filing_url}")
        print(f"DQC rules enabled: {use_dqc_rules}")
        
        # Perform validation
        success, output, error = validate_filing(filing_url, use_dqc_rules)
        
        # Determine status
        validation_status = 'success' if success else 'error'
        
        # Save to DynamoDB (if table name is configured)
        dynamodb_result = None
        if os.environ.get('DYNAMODB_TABLE_NAME'):
            print(f"Saving validation result to DynamoDB table: {os.environ.get('DYNAMODB_TABLE_NAME')}")
            dynamodb_result = save_to_dynamodb(
                filing_url=filing_url,
                status=validation_status,
                validation_output=output,
                dqc_rules_enabled=use_dqc_rules,
                validation_errors=error if error else None
            )
            
            if dynamodb_result.get('success'):
                print(f"Successfully saved to DynamoDB at timestamp: {dynamodb_result.get('timestamp')}")
            else:
                print(f"Failed to save to DynamoDB: {dynamodb_result.get('error')}")
        else:
            print("DYNAMODB_TABLE_NAME not set, skipping DynamoDB save")
        
        # Send to SQS for next stage processing (only for successful validations)
        sqs_result = None
        if validation_status == 'success' and os.environ.get('SQS_QUEUE_URL'):
            print(f"Sending successful validation to SQS queue: {os.environ.get('SQS_QUEUE_URL')}")
            sqs_result = send_to_sqs(
                filing_url=filing_url,
                validation_output=output,
                dqc_rules_enabled=use_dqc_rules,
                timestamp=dynamodb_result.get('timestamp') if dynamodb_result and dynamodb_result.get('success') else None
            )
            
            if sqs_result.get('success'):
                print(f"Successfully sent to SQS with message ID: {sqs_result.get('message_id')}")
            else:
                print(f"Failed to send to SQS: {sqs_result.get('error')}")
        elif validation_status == 'success':
            print("SQS_QUEUE_URL not set, skipping SQS send")
        else:
            print(f"Validation status is '{validation_status}', skipping SQS send (only successful validations are sent)")
        
        # Send to SNS to notify filer (only for failed validations)
        sns_result = None
        if validation_status == 'error' and os.environ.get('SNS_TOPIC_ARN'):
            print(f"Sending validation failure notification to SNS topic: {os.environ.get('SNS_TOPIC_ARN')}")
            sns_result = send_to_sns(
                filing_url=filing_url,
                validation_output=output,
                validation_errors=error,
                dqc_rules_enabled=use_dqc_rules,
                timestamp=dynamodb_result.get('timestamp') if dynamodb_result and dynamodb_result.get('success') else None
            )
            
            if sns_result.get('success'):
                print(f"Successfully sent to SNS with message ID: {sns_result.get('message_id')}")
            else:
                print(f"Failed to send to SNS: {sns_result.get('error')}")
        elif validation_status == 'error':
            print("SNS_TOPIC_ARN not set, skipping SNS notification")
        else:
            print(f"Validation status is '{validation_status}', skipping SNS notification (only failed validations are notified)")
        
        # Prepare response
        response_body = {
            'status': validation_status,
            'filing_url': filing_url,
            'dqc_rules_enabled': use_dqc_rules,
            'validation_output': output,
            'validation_errors': error if error else None
        }
        
        # Include DynamoDB save result if attempted
        if dynamodb_result:
            response_body['dynamodb_save'] = {
                'success': dynamodb_result.get('success'),
                'timestamp': dynamodb_result.get('timestamp') if dynamodb_result.get('success') else None,
                'error': dynamodb_result.get('error') if not dynamodb_result.get('success') else None
            }
        
        # Include SQS send result if attempted
        if sqs_result:
            response_body['sqs_send'] = {
                'success': sqs_result.get('success'),
                'message_id': sqs_result.get('message_id') if sqs_result.get('success') else None,
                'error': sqs_result.get('error') if not sqs_result.get('success') else None
            }
        
        # Include SNS send result if attempted
        if sns_result:
            response_body['sns_send'] = {
                'success': sns_result.get('success'),
                'message_id': sns_result.get('message_id') if sns_result.get('success') else None,
                'error': sns_result.get('error') if not sns_result.get('success') else None
            }
        
        return {
            'statusCode': 200 if success else 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
        "use_dqc_rules": True
    }
    
    result = lambda_handler(test_event, None)
    print("\n" + "="*80)
    print("Lambda Response:")
    print(json.dumps(result, indent=2))
