# Lambda Event Examples

This directory contains example event payloads for testing the AWS Lambda function.

## Event Files

### event_with_dqc.json
Example event that enables DQC/DQCRT validation rules (default behavior).

### event_without_dqc.json
Example event that disables DQC rules, performing only basic EFM validation.

## Usage

### Testing Locally

```bash
# Test with DQC rules enabled
python lambda_handler.py

# Or test with specific event file
python -c "
import json
from lambda_handler import lambda_handler

with open('lambda_examples/event_with_dqc.json') as f:
    event = json.load(f)
    
result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

### Testing with AWS CLI

```bash
# Invoke Lambda with DQC rules
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_with_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json

# Invoke Lambda without DQC rules
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_without_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json
```

### Testing with Docker

```bash
# Run container locally
docker run -p 9000:8080 xbrl-validator:latest

# In another terminal, invoke with test event
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -d @lambda_examples/event_with_dqc.json
```

## Event Structure

```json
{
  "filing_url": "string (required) - URL or S3 path to XBRL filing",
  "use_dqc_rules": "boolean (optional) - Enable/disable DQC rules, default: true"
}
```

## Response Structure

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "status": "success",
    "filing_url": "https://...",
    "dqc_rules_enabled": true,
    "validation_output": "Validation messages...",
    "validation_errors": null
  }
}
```
