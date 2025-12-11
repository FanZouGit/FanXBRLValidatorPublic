"""
SQS helper module for sending XBRL validation results to next stage processing.

This module provides functionality to send messages to AWS SQS queue for
filings that successfully pass validation.
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError


class SQSHelper:
    """Helper class for SQS operations related to validation results."""
    
    def __init__(self, queue_url: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize SQS helper.
        
        :param queue_url: SQS queue URL. If not provided, uses SQS_QUEUE_URL
                         environment variable.
        :param region_name: AWS region name. If not provided, uses AWS_DEFAULT_REGION
                           environment variable or boto3 default.
        """
        self.queue_url = queue_url or os.environ.get('SQS_QUEUE_URL')
        if not self.queue_url:
            raise ValueError(
                "SQS queue URL must be provided either as parameter or "
                "via SQS_QUEUE_URL environment variable"
            )
        
        # Initialize SQS client with optional region
        region = region_name or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            self.sqs = boto3.client('sqs', region_name=region)
        else:
            self.sqs = boto3.client('sqs')
    
    def send_validation_success(
        self,
        filing_url: str,
        validation_output: str,
        dqc_rules_enabled: bool = True,
        timestamp: Optional[str] = None,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send validation success message to SQS for next stage processing.
        
        :param filing_url: URL of the XBRL filing that passed validation
        :param validation_output: Full validation output text
        :param dqc_rules_enabled: Whether DQC rules were enabled
        :param timestamp: ISO 8601 timestamp of validation (defaults to current time)
        :param message_attributes: Additional message attributes
        :return: Dictionary with send operation result
        """
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare the message body
        message_body = {
            'filing_url': filing_url,
            'timestamp': timestamp,
            'status': 'success',
            'dqc_rules_enabled': dqc_rules_enabled,
            'validation_output': validation_output
        }
        
        # Prepare message attributes for SQS filtering if needed
        msg_attributes = {
            'status': {
                'StringValue': 'success',
                'DataType': 'String'
            },
            'filing_url': {
                'StringValue': filing_url,
                'DataType': 'String'
            },
            'dqc_enabled': {
                'StringValue': str(dqc_rules_enabled).lower(),
                'DataType': 'String'
            }
        }
        
        # Add custom attributes if provided
        if message_attributes:
            msg_attributes.update(message_attributes)
        
        try:
            # Send message to SQS
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes=msg_attributes
            )
            
            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'timestamp': timestamp,
                'queue_url': self.queue_url
            }
        
        except ClientError as e:
            error_msg = f"Error sending to SQS: {e.response['Error']['Message']}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_code': e.response['Error']['Code']
            }
        except Exception as e:
            error_msg = f"Unexpected error sending to SQS: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }


def send_to_sqs(
    filing_url: str,
    validation_output: str,
    dqc_rules_enabled: bool = True,
    timestamp: Optional[str] = None,
    queue_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send validation success message to SQS.
    
    :param filing_url: URL of the XBRL filing that passed validation
    :param validation_output: Full validation output text
    :param dqc_rules_enabled: Whether DQC rules were enabled
    :param timestamp: ISO 8601 timestamp of validation (optional)
    :param queue_url: SQS queue URL (optional)
    :return: Dictionary with send operation result
    """
    try:
        helper = SQSHelper(queue_url)
        return helper.send_validation_success(
            filing_url=filing_url,
            validation_output=validation_output,
            dqc_rules_enabled=dqc_rules_enabled,
            timestamp=timestamp
        )
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
