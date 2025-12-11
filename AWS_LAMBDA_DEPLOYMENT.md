# AWS Lambda Deployment Guide

This guide explains how to deploy the XBRL Validator as an AWS Lambda function using a Docker container image.

## Overview

The XBRL Validator can be deployed to AWS Lambda as a containerized application. This allows you to:
- Validate XBRL filings on-demand without maintaining servers
- Scale automatically based on load
- Pay only for actual validation time
- Integrate with other AWS services (S3, API Gateway, etc.)

## Architecture

```
API Gateway / S3 Event / Direct Invoke
    ↓
AWS Lambda (Container)
    ├── lambda_handler.py (Entry point)
    ├── dynamodb_helper.py (DynamoDB integration)
    ├── sqs_helper.py (SQS integration)
    ├── sns_helper.py (SNS integration)
    ├── validate_filing.py (Validation logic)
    └── Arelle/ (XBRL engine + plugins)
    ↓
    ├─→ DynamoDB Table (Optional)
    │   └── Validation Results Storage
    │
    ├─→ SQS Queue (Optional)
    │   └── Successful Validations for Next Stage Processing
    │
    └─→ SNS Topic (Optional)
        └── Failed Validation Notifications to Filer
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with your credentials
3. **Docker** installed locally
4. **Amazon ECR** repository created

## Setup Steps

### 1. Create an ECR Repository

```bash
# Create ECR repository for the Lambda image
aws ecr create-repository \
    --repository-name xbrl-validator \
    --region us-east-1
```

### 2. Build the Docker Image

```bash
# Build the Lambda-compatible Docker image
docker build -f Dockerfile.lambda -t xbrl-validator:latest .

# This may take several minutes as it:
# - Installs system dependencies
# - Installs Python packages
# - Copies Arelle application
# - Clones EDGAR and xule plugins
```

### 3. Authenticate Docker to ECR

```bash
# Get authentication token and login
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    <your-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### 4. Tag and Push Image to ECR

```bash
# Tag the image
docker tag xbrl-validator:latest \
    <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest

# Push to ECR
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest
```

### 5. Create Lambda Function

#### Option A: Using AWS Console

1. Go to AWS Lambda Console
2. Click "Create function"
3. Select "Container image"
4. Function name: `xbrl-validator`
5. Container image URI: Browse and select your ECR image
6. Architecture: x86_64
7. Click "Create function"

#### Option B: Using AWS CLI

```bash
# Create Lambda function from container image
aws lambda create-function \
    --function-name xbrl-validator \
    --package-type Image \
    --code ImageUri=<your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest \
    --role arn:aws:iam::<your-account-id>:role/<lambda-execution-role> \
    --memory-size 2048 \
    --timeout 300 \
    --region us-east-1
```

### 6. Configure Lambda Settings

Important configuration settings:

- **Memory**: 2048 MB or higher (XBRL validation is memory-intensive)
- **Timeout**: 300 seconds (5 minutes) or higher for complex filings
- **Ephemeral storage**: 1024 MB or higher for temporary files
- **Environment variables** (optional):
  - `LOG_LEVEL`: `INFO` or `DEBUG`
  - `DYNAMODB_TABLE_NAME`: Name of DynamoDB table to store validation results (optional)
  - `SQS_QUEUE_URL`: URL of SQS queue for successful validations (optional)
  - `SNS_TOPIC_ARN`: ARN of SNS topic for failed validation notifications (optional)

```bash
# Update Lambda configuration
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --memory-size 2048 \
    --timeout 300 \
    --ephemeral-storage Size=1024
```

### 7. (Optional) Setup DynamoDB for Validation Results

The Lambda function can automatically save validation results to DynamoDB for historical tracking and analysis.

#### Create DynamoDB Table

```bash
# Create DynamoDB table for validation results
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

#### Update Lambda IAM Role

Add DynamoDB permissions to the Lambda execution role:

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

Apply the policy:

```bash
# Create policy
aws iam create-policy \
    --policy-name xbrl-validator-dynamodb-policy \
    --policy-document file://dynamodb-policy.json

# Attach to Lambda role
aws iam attach-role-policy \
    --role-name <lambda-execution-role> \
    --policy-arn arn:aws:iam::<account-id>:policy/xbrl-validator-dynamodb-policy
```

#### Configure Environment Variable

```bash
# Set DynamoDB table name in Lambda environment
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --environment Variables={DYNAMODB_TABLE_NAME=xbrl-validation-results}
```

**Note**: If `DYNAMODB_TABLE_NAME` is not set, the Lambda will still work but won't save results to DynamoDB.

### 8. (Optional) Setup SQS for Next Stage Processing

The Lambda function can automatically send successful validation results to an SQS queue for downstream processing.

#### Create SQS Queue

```bash
# Create SQS queue for successful validations
aws sqs create-queue \
    --queue-name xbrl-successful-validations \
    --region us-east-1

# Get the queue URL (save this for configuration)
aws sqs get-queue-url \
    --queue-name xbrl-successful-validations \
    --region us-east-1
```

#### Update Lambda IAM Role

Add SQS permissions to the Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:GetQueueUrl"
      ],
      "Resource": "arn:aws:sqs:us-east-1:<account-id>:xbrl-successful-validations"
    }
  ]
}
```

Apply the policy:

```bash
# Create policy
aws iam create-policy \
    --policy-name xbrl-validator-sqs-policy \
    --policy-document file://sqs-policy.json

# Attach to Lambda role
aws iam attach-role-policy \
    --role-name <lambda-execution-role> \
    --policy-arn arn:aws:iam::<account-id>:policy/xbrl-validator-sqs-policy
```

#### Configure Environment Variable

```bash
# Set SQS queue URL in Lambda environment
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --environment Variables={SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/<account-id>/xbrl-successful-validations}
```

**Note**: 
- If `SQS_QUEUE_URL` is not set, the Lambda will still work but won't send messages to SQS
- Only filings that **pass validation** (status='success') are sent to SQS
- Failed validations are NOT sent to SQS

#### SQS Message Format

Messages sent to SQS contain:

```json
{
  "filing_url": "https://www.sec.gov/path/to/filing.htm",
  "timestamp": "2024-12-11T18:30:45.123456+00:00",
  "status": "success",
  "dqc_rules_enabled": true,
  "validation_output": "[info] validated in 2.34 secs"
}
```

Message attributes for filtering:
- `status`: "success"
- `filing_url`: The filing URL
- `dqc_enabled`: "true" or "false"

### 9. (Optional) Setup SNS for Failed Validation Notifications

The Lambda function can automatically send notifications via SNS when validation fails, allowing filers to be notified.

#### Create SNS Topic

```bash
# Create SNS topic for failed validation notifications
aws sns create-topic \
    --name xbrl-validation-failures \
    --region us-east-1

# Get the topic ARN (save this for configuration)
aws sns list-topics --region us-east-1 | grep xbrl-validation-failures
```

#### Subscribe Email/SMS to Topic

```bash
# Subscribe an email address to receive notifications
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:<account-id>:xbrl-validation-failures \
    --protocol email \
    --notification-endpoint filer@example.com

# Or subscribe an SMS number
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:<account-id>:xbrl-validation-failures \
    --protocol sms \
    --notification-endpoint +1234567890
```

#### Update Lambda IAM Role

Add SNS permissions to the Lambda execution role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:us-east-1:<account-id>:xbrl-validation-failures"
    }
  ]
}
```

Apply the policy:

```bash
# Create policy
aws iam create-policy \
    --policy-name xbrl-validator-sns-policy \
    --policy-document file://sns-policy.json

# Attach to Lambda role
aws iam attach-role-policy \
    --role-name <lambda-execution-role> \
    --policy-arn arn:aws:iam::<account-id>:policy/xbrl-validator-sns-policy
```

#### Configure Environment Variable

```bash
# Set SNS topic ARN in Lambda environment
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --environment Variables={SNS_TOPIC_ARN=arn:aws:sns:us-east-1:<account-id>:xbrl-validation-failures}
```

**Note**: 
- If `SNS_TOPIC_ARN` is not set, the Lambda will still work but won't send notifications
- Only filings that **fail validation** (status='error') trigger SNS notifications
- Successful validations are NOT sent to SNS

#### SNS Notification Format

Notifications sent to SNS contain:

**Subject**: `XBRL Validation Failure: [filing_url]`

**Message Body**:
```json
{
  "filing_url": "https://www.sec.gov/path/to/filing.htm",
  "timestamp": "2024-12-11T18:30:45.123456+00:00",
  "status": "error",
  "dqc_rules_enabled": true,
  "validation_output": "[error] Validation failed...",
  "validation_errors": "Error details..."
}
```

Message attributes for filtering:
- `status`: "error"
- `filing_url`: The filing URL
- `dqc_enabled`: "true" or "false"


## Usage

### Invoke Lambda Function Directly

```bash
# Create test event file
cat > event.json << 'EOF'
{
  "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
  "use_dqc_rules": true
}
EOF

# Invoke Lambda function
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://event.json \
    --cli-binary-format raw-in-base64-out \
    response.json

# View response
cat response.json | jq .
```

### Event Payload Structure

```json
{
  "filing_url": "https://www.sec.gov/path/to/filing.htm",
  "use_dqc_rules": true
}
```

**Parameters:**
- `filing_url` (required): URL or S3 path to the XBRL filing
- `use_dqc_rules` (optional): Boolean, default `true`. Set to `false` to disable DQC validation

### Response Structure

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{\"status\":\"success\",\"filing_url\":\"...\",\"validation_output\":\"...\",\"dynamodb_save\":{...}}"
}
```

The `body` field contains a JSON string with:
- `status`: "success" or "error"
- `filing_url`: The filing that was validated
- `dqc_rules_enabled`: Whether DQC rules were used
- `validation_output`: Validation messages and results
- `validation_errors`: Any errors encountered (if applicable)
- `dynamodb_save`: (Optional) Result of saving to DynamoDB
  - `success`: Boolean indicating if save was successful
  - `timestamp`: ISO 8601 timestamp when saved (if successful)
  - `error`: Error message (if save failed)
- `sqs_send`: (Optional) Result of sending to SQS (only for successful validations)
  - `success`: Boolean indicating if send was successful
  - `message_id`: SQS message ID (if successful)
  - `error`: Error message (if send failed)
- `sns_send`: (Optional) Result of sending to SNS (only for failed validations)
  - `success`: Boolean indicating if send was successful
  - `message_id`: SNS message ID (if successful)
  - `error`: Error message (if send failed)

**Notes**: 
- The `dynamodb_save` field only appears if `DYNAMODB_TABLE_NAME` environment variable is configured
- The `sqs_send` field only appears if `SQS_QUEUE_URL` is configured and validation succeeds
- The `sns_send` field only appears if `SNS_TOPIC_ARN` is configured and validation fails

## Integration Options

### 1. API Gateway Integration

Create a REST API to expose the Lambda function via HTTP:

```bash
# Create REST API
aws apigateway create-rest-api \
    --name xbrl-validator-api \
    --description "XBRL Validation API"

# Configure API Gateway to invoke Lambda
# (Additional configuration steps required)
```

### 2. S3 Event Trigger

Automatically validate filings when uploaded to S3:

```bash
# Add S3 trigger to Lambda
aws lambda add-permission \
    --function-name xbrl-validator \
    --statement-id s3-invoke \
    --action lambda:InvokeFunction \
    --principal s3.amazonaws.com \
    --source-arn arn:aws:s3:::your-filings-bucket

# Configure S3 bucket notification
# (S3 console or CLI configuration)
```

### 3. EventBridge Schedule

Run validations on a schedule:

```bash
# Create EventBridge rule
aws events put-rule \
    --name daily-xbrl-validation \
    --schedule-expression "rate(1 day)"

# Add Lambda as target
aws events put-targets \
    --rule daily-xbrl-validation \
    --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:<account-id>:function:xbrl-validator"
```

## Local Testing

Test the Lambda function locally using Docker:

```bash
# Run container locally
docker run -p 9000:8080 xbrl-validator:latest

# In another terminal, invoke the function
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -d '{
      "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
      "use_dqc_rules": true
    }'
```

## Monitoring and Logging

### CloudWatch Logs

Lambda automatically logs to CloudWatch:

```bash
# View logs
aws logs tail /aws/lambda/xbrl-validator --follow
```

### CloudWatch Metrics

Monitor Lambda performance:
- Invocations
- Duration
- Error count
- Throttles
- Memory usage

## Cost Estimation

AWS Lambda pricing (as of 2024):
- **Compute**: $0.0000166667 per GB-second
- **Requests**: $0.20 per 1M requests

Example calculation for 2GB memory, 60-second validation:
- Per invocation: ~$0.002
- 1,000 validations: ~$2.20

Plus ECR storage costs (~$0.10/GB/month).

## Troubleshooting

### Out of Memory Errors

Increase Lambda memory:
```bash
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --memory-size 3008
```

### Timeout Errors

Increase Lambda timeout:
```bash
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --timeout 600
```

### Plugin Not Found Errors

Verify plugins were cloned during Docker build:
```bash
docker run --entrypoint /bin/bash xbrl-validator:latest -c \
    "ls -la /var/task/Arelle/arelle/plugin/"
```

### Network Connectivity Issues

Ensure Lambda has internet access:
- If in VPC, add NAT Gateway
- Or use public subnet with internet gateway

## Updates and Maintenance

### Update Lambda Image

```bash
# Rebuild image
docker build -f Dockerfile.lambda -t xbrl-validator:latest .

# Push to ECR
docker tag xbrl-validator:latest \
    <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest
docker push <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest

# Update Lambda to use new image
aws lambda update-function-code \
    --function-name xbrl-validator \
    --image-uri <your-account-id>.dkr.ecr.us-east-1.amazonaws.com/xbrl-validator:latest
```

### Update Plugins

Plugins are cloned during Docker build. To update:
1. Rebuild the Docker image (pulls latest plugin versions)
2. Push to ECR
3. Update Lambda function

## Security Best Practices

1. **IAM Role**: Use least-privilege IAM role for Lambda
2. **VPC**: Consider running Lambda in VPC for additional isolation
3. **Secrets**: Store sensitive data in AWS Secrets Manager
4. **Encryption**: Enable encryption at rest for ECR images
5. **Monitoring**: Set up CloudWatch alarms for errors and throttles

## Advanced Configuration

### Environment Variables

```bash
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --environment Variables={LOG_LEVEL=DEBUG,CACHE_DIR=/tmp}
```

### VPC Configuration

```bash
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --vpc-config SubnetIds=subnet-xxx,SecurityGroupIds=sg-xxx
```

### Concurrent Execution Limits

```bash
aws lambda put-function-concurrency \
    --function-name xbrl-validator \
    --reserved-concurrent-executions 10
```

## Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Container Image Support](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [ECR Documentation](https://docs.aws.amazon.com/ecr/)

## Support

For issues:
- **Lambda Deployment**: AWS Support
- **XBRL Validation**: See main [README.md](README.md)
- **Docker Issues**: Check Dockerfile.lambda configuration
