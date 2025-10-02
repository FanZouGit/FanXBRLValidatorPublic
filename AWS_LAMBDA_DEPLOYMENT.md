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
    ├── validate_filing.py (Validation logic)
    └── Arelle/ (XBRL engine + plugins)
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

```bash
# Update Lambda configuration
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --memory-size 2048 \
    --timeout 300 \
    --ephemeral-storage Size=1024
```

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
  "body": "{\"status\":\"success\",\"filing_url\":\"...\",\"validation_output\":\"...\"}"
}
```

The `body` field contains a JSON string with:
- `status`: "success" or "error"
- `filing_url`: The filing that was validated
- `dqc_rules_enabled`: Whether DQC rules were used
- `validation_output`: Validation messages and results
- `validation_errors`: Any errors encountered (if applicable)

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
