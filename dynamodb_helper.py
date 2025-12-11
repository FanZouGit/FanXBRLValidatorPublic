"""
DynamoDB helper module for saving XBRL validation results.

This module provides functionality to save validation results to AWS DynamoDB,
including the filing URL, validation status, output, and timestamp.
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


class DynamoDBHelper:
    """Helper class for DynamoDB operations related to validation results."""
    
    def __init__(self, table_name: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize DynamoDB helper.
        
        :param table_name: DynamoDB table name. If not provided, uses DYNAMODB_TABLE_NAME
                          environment variable.
        :param region_name: AWS region name. If not provided, uses AWS_DEFAULT_REGION
                           environment variable or boto3 default.
        """
        self.table_name = table_name or os.environ.get('DYNAMODB_TABLE_NAME')
        if not self.table_name:
            raise ValueError(
                "DynamoDB table name must be provided either as parameter or "
                "via DYNAMODB_TABLE_NAME environment variable"
            )
        
        # Initialize DynamoDB resource with optional region
        region = region_name or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            self.dynamodb = boto3.resource('dynamodb', region_name=region)
        else:
            self.dynamodb = boto3.resource('dynamodb')
        
        self.table = self.dynamodb.Table(self.table_name)
    
    def save_validation_result(
        self,
        filing_url: str,
        status: str,
        validation_output: str,
        dqc_rules_enabled: bool = True,
        validation_errors: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save validation result to DynamoDB.
        
        :param filing_url: URL of the XBRL filing that was validated
        :param status: Validation status ('success' or 'error')
        :param validation_output: Full validation output text
        :param dqc_rules_enabled: Whether DQC rules were enabled
        :param validation_errors: Error messages if validation failed
        :param metadata: Additional metadata to store
        :return: Dictionary with save operation result
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare the item to save
        item = {
            'filing_url': filing_url,
            'timestamp': timestamp,
            'status': status,
            'dqc_rules_enabled': dqc_rules_enabled,
            'validation_output': validation_output,
        }
        
        # Add optional fields
        if validation_errors:
            item['validation_errors'] = validation_errors
        
        if metadata:
            item['metadata'] = metadata
        
        try:
            # Save to DynamoDB
            response = self.table.put_item(Item=item)
            
            return {
                'success': True,
                'timestamp': timestamp,
                'table_name': self.table_name,
                'response': response
            }
        
        except ClientError as e:
            error_msg = f"Error saving to DynamoDB: {e.response['Error']['Message']}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_code': e.response['Error']['Code']
            }
        except Exception as e:
            error_msg = f"Unexpected error saving to DynamoDB: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_validation_result(
        self,
        filing_url: str,
        timestamp: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve validation result from DynamoDB.
        
        :param filing_url: URL of the XBRL filing
        :param timestamp: Specific timestamp to retrieve. If not provided, gets the latest.
        :return: Validation result item or None if not found
        """
        try:
            if timestamp:
                # Get specific item
                response = self.table.get_item(
                    Key={
                        'filing_url': filing_url,
                        'timestamp': timestamp
                    }
                )
                return response.get('Item')
            else:
                # Query for the filing_url and get the most recent
                response = self.table.query(
                    KeyConditionExpression=Key('filing_url').eq(filing_url),
                    ScanIndexForward=False,  # Descending order (newest first)
                    Limit=1
                )
                items = response.get('Items', [])
                return items[0] if items else None
        
        except ClientError as e:
            print(f"Error retrieving from DynamoDB: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            print(f"Unexpected error retrieving from DynamoDB: {str(e)}")
            return None


def save_to_dynamodb(
    filing_url: str,
    status: str,
    validation_output: str,
    dqc_rules_enabled: bool = True,
    validation_errors: Optional[str] = None,
    table_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to save validation result to DynamoDB.
    
    :param filing_url: URL of the XBRL filing that was validated
    :param status: Validation status ('success' or 'error')
    :param validation_output: Full validation output text
    :param dqc_rules_enabled: Whether DQC rules were enabled
    :param validation_errors: Error messages if validation failed
    :param table_name: DynamoDB table name (optional)
    :return: Dictionary with save operation result
    """
    try:
        helper = DynamoDBHelper(table_name)
        return helper.save_validation_result(
            filing_url=filing_url,
            status=status,
            validation_output=validation_output,
            dqc_rules_enabled=dqc_rules_enabled,
            validation_errors=validation_errors
        )
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
