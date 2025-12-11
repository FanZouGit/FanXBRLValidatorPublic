# DynamoDB Table Schema for XBRL Validation Results

## Table Overview

This table stores validation results from the XBRL validator Lambda function, providing a historical record of all validated filings.

## Table Name

Default: `xbrl-validation-results` (configurable via `DYNAMODB_TABLE_NAME` environment variable)

## Primary Key

The table uses a composite primary key:

- **Partition Key**: `filing_url` (String)
  - The URL of the XBRL filing that was validated
  - Example: `https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm`

- **Sort Key**: `timestamp` (String)
  - ISO 8601 timestamp in UTC when the validation was performed
  - Example: `2024-12-11T18:30:45.123456+00:00`

This composite key allows:
- Quick lookup of all validation results for a specific filing
- Chronological ordering of validation attempts
- Historical tracking of validation results over time

## Attributes

| Attribute Name | Type | Required | Description |
|----------------|------|----------|-------------|
| `filing_url` | String | Yes | URL of the XBRL filing (partition key) |
| `timestamp` | String | Yes | ISO 8601 timestamp in UTC (sort key) |
| `status` | String | Yes | Validation status: "success" or "error" |
| `dqc_rules_enabled` | Boolean | Yes | Whether DQC rules were enabled during validation |
| `validation_output` | String | Yes | Full validation output text including all messages |
| `validation_errors` | String | No | Error messages if validation failed |
| `metadata` | Map | No | Additional metadata (extensible for future use) |

## Example Item

```json
{
  "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
  "timestamp": "2024-12-11T18:30:45.123456+00:00",
  "status": "success",
  "dqc_rules_enabled": true,
  "validation_output": "[info] Activation of plug-in Edgar Renderer successful...\n[EFM.6.05.20] DEI facts are correct...\n[info] validated in 2.34 secs",
  "validation_errors": null
}
```

## Table Creation

### Using AWS CLI

```bash
aws dynamodb create-table \
    --table-name xbrl-validation-results \
    --attribute-definitions \
        AttributeName=filing_url,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=filing_url,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### Using AWS CloudFormation

```yaml
Resources:
  XBRLValidationResultsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: xbrl-validation-results
      AttributeDefinitions:
        - AttributeName: filing_url
          AttributeType: S
        - AttributeName: timestamp
          AttributeType: S
      KeySchema:
        - AttributeName: filing_url
          KeyType: HASH
        - AttributeName: timestamp
          KeyType: RANGE
      BillingMode: PAY_PER_REQUEST
      Tags:
        - Key: Purpose
          Value: XBRL Validation Results Storage
```

### Using Terraform

```hcl
resource "aws_dynamodb_table" "xbrl_validation_results" {
  name           = "xbrl-validation-results"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "filing_url"
  range_key      = "timestamp"

  attribute {
    name = "filing_url"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Purpose = "XBRL Validation Results Storage"
  }
}
```

## Common Queries

### Get Latest Validation for a Filing

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('xbrl-validation-results')

response = table.query(
    KeyConditionExpression='filing_url = :url',
    ExpressionAttributeValues={
        ':url': 'https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm'
    },
    ScanIndexForward=False,  # Descending order (newest first)
    Limit=1
)

latest_result = response['Items'][0] if response['Items'] else None
```

### Get All Validations for a Filing

```python
response = table.query(
    KeyConditionExpression='filing_url = :url',
    ExpressionAttributeValues={
        ':url': 'https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm'
    }
)

all_validations = response['Items']
```

### Get Specific Validation by Timestamp

```python
response = table.get_item(
    Key={
        'filing_url': 'https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm',
        'timestamp': '2024-12-11T18:30:45.123456+00:00'
    }
)

validation_result = response.get('Item')
```

## IAM Permissions

The Lambda function requires the following DynamoDB permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:<account-id>:table/xbrl-validation-results"
    }
  ]
}
```

## Cost Considerations

With **PAY_PER_REQUEST** billing:
- **Write**: ~$1.25 per million write requests
- **Read**: ~$0.25 per million read requests
- **Storage**: ~$0.25 per GB-month

Example monthly cost for 10,000 validations:
- 10,000 writes: ~$0.0125
- Average item size: ~10 KB
- Storage: 100 MB = ~$0.025/month
- **Total**: ~$0.04/month

## Backup and Retention

Consider enabling:
1. **Point-in-time recovery** for data protection
2. **On-demand backups** for long-term retention
3. **DynamoDB Streams** for real-time processing
4. **TTL (Time To Live)** if you want automatic deletion of old records

### Enable Point-in-Time Recovery

```bash
aws dynamodb update-continuous-backups \
    --table-name xbrl-validation-results \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### Configure TTL (Optional)

To automatically delete records older than a certain time, add a TTL attribute:

```bash
aws dynamodb update-time-to-live \
    --table-name xbrl-validation-results \
    --time-to-live-specification Enabled=true,AttributeName=ttl
```

## Monitoring

Monitor table performance using CloudWatch metrics:
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `UserErrors`
- `SystemErrors`

## Related Documentation

- [AWS_LAMBDA_DEPLOYMENT.md](AWS_LAMBDA_DEPLOYMENT.md) - Lambda deployment guide
- [lambda_handler.py](lambda_handler.py) - Lambda function implementation
- [dynamodb_helper.py](dynamodb_helper.py) - DynamoDB helper module
