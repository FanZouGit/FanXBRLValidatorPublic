"""
SNS helper module for sending XBRL validation failure notifications.

This module provides functionality to send notifications to AWS SNS topic for
filings that fail validation.
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError


class SNSHelper:
    """Helper class for SNS operations related to validation failures."""
    
    def __init__(self, topic_arn: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize SNS helper.
        
        :param topic_arn: SNS topic ARN. If not provided, uses SNS_TOPIC_ARN
                         environment variable.
        :param region_name: AWS region name. If not provided, uses AWS_DEFAULT_REGION
                           environment variable or boto3 default.
        """
        self.topic_arn = topic_arn or os.environ.get('SNS_TOPIC_ARN')
        if not self.topic_arn:
            raise ValueError(
                "SNS topic ARN must be provided either as parameter or "
                "via SNS_TOPIC_ARN environment variable"
            )
        
        # Initialize SNS client with optional region
        region = region_name or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            self.sns = boto3.client('sns', region_name=region)
        else:
            self.sns = boto3.client('sns')
    
    def send_validation_failure(
        self,
        filing_url: str,
        validation_output: str,
        validation_errors: Optional[str] = None,
        dqc_rules_enabled: bool = True,
        timestamp: Optional[str] = None,
        message_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send validation failure notification to SNS.
        
        :param filing_url: URL of the XBRL filing that failed validation
        :param validation_output: Full validation output text
        :param validation_errors: Error messages from validation
        :param dqc_rules_enabled: Whether DQC rules were enabled
        :param timestamp: ISO 8601 timestamp of validation (defaults to current time)
        :param message_attributes: Additional message attributes
        :return: Dictionary with send operation result
        """
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare the notification message
        subject = f"XBRL Validation Failure: {filing_url}"
        
        message_body = {
            'filing_url': filing_url,
            'timestamp': timestamp,
            'status': 'error',
            'dqc_rules_enabled': dqc_rules_enabled,
            'validation_output': validation_output,
            'validation_errors': validation_errors
        }
        
        # Create a formatted text message
        text_message = f"""XBRL Validation Failure Notification

Filing URL: {filing_url}
Timestamp: {timestamp}
DQC Rules Enabled: {dqc_rules_enabled}

Validation Output:
{validation_output}
"""
        
        if validation_errors:
            text_message += f"\nValidation Errors:\n{validation_errors}"
        
        # Prepare message attributes for SNS filtering if needed
        msg_attributes = {
            'status': {
                'StringValue': 'error',
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
            # Send notification to SNS
            response = self.sns.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=json.dumps(message_body, indent=2),
                MessageAttributes=msg_attributes
            )
            
            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'timestamp': timestamp,
                'topic_arn': self.topic_arn
            }
        
        except ClientError as e:
            error_msg = f"Error sending to SNS: {e.response['Error']['Message']}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_code': e.response['Error']['Code']
            }
        except Exception as e:
            error_msg = f"Unexpected error sending to SNS: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }


def send_to_sns(
    filing_url: str,
    validation_output: str,
    validation_errors: Optional[str] = None,
    dqc_rules_enabled: bool = True,
    timestamp: Optional[str] = None,
    topic_arn: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to send validation failure notification to SNS.
    
    :param filing_url: URL of the XBRL filing that failed validation
    :param validation_output: Full validation output text
    :param validation_errors: Error messages from validation
    :param dqc_rules_enabled: Whether DQC rules were enabled
    :param timestamp: ISO 8601 timestamp of validation (optional)
    :param topic_arn: SNS topic ARN (optional)
    :return: Dictionary with send operation result
    """
    try:
        helper = SNSHelper(topic_arn)
        return helper.send_validation_failure(
            filing_url=filing_url,
            validation_output=validation_output,
            validation_errors=validation_errors,
            dqc_rules_enabled=dqc_rules_enabled,
            timestamp=timestamp
        )
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
