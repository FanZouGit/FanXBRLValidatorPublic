# AWS Lambda Testing Guide

This guide provides instructions for testing the XBRL Validator Lambda function at various stages of deployment.

## Testing Stages

1. **Syntax Validation** - Verify Python code is valid
2. **Local Docker Testing** - Test the container locally
3. **Lambda Function Testing** - Test deployed Lambda function
4. **Integration Testing** - Test with API Gateway or other services

## 1. Syntax Validation

Before building the Docker image, verify Python syntax:

```bash
# Check lambda_handler.py syntax
python3 -m py_compile lambda_handler.py

# Check validate_filing.py syntax  
python3 -m py_compile validate_filing.py
```

## 2. Local Docker Testing

### Build the Image

```bash
# Use the build script
./build_lambda.sh

# Or build manually
docker build -f Dockerfile.lambda -t xbrl-validator:latest .
```

### Run Container Locally

AWS Lambda Runtime Interface Emulator allows local testing:

```bash
# Start the container
docker run -p 9000:8080 xbrl-validator:latest
```

### Invoke Function Locally

In another terminal:

```bash
# Test with DQC rules enabled
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -H "Content-Type: application/json" \
    -d '{
      "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
      "use_dqc_rules": true
    }'

# Test with DQC rules disabled
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -H "Content-Type: application/json" \
    -d '{
      "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
      "use_dqc_rules": false
    }'
```

Or use the example event files:

```bash
# With DQC rules
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -H "Content-Type: application/json" \
    -d @lambda_examples/event_with_dqc.json

# Without DQC rules
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
    -H "Content-Type: application/json" \
    -d @lambda_examples/event_without_dqc.json
```

### Verify Container Contents

Check that plugins were installed correctly:

```bash
# List plugin directory
docker run --entrypoint /bin/bash xbrl-validator:latest -c \
    "ls -la /var/task/Arelle/arelle/plugin/"

# Verify EDGAR plugin
docker run --entrypoint /bin/bash xbrl-validator:latest -c \
    "ls -la /var/task/Arelle/arelle/plugin/EDGAR/"

# Verify xule plugin
docker run --entrypoint /bin/bash xbrl-validator:latest -c \
    "ls -la /var/task/Arelle/arelle/plugin/xule/"
```

## 3. Lambda Function Testing

After deploying to AWS Lambda:

### Test with AWS CLI

```bash
# Basic invocation
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_with_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json

# View the response
cat response.json | jq .

# Parse the body (which is a JSON string)
cat response.json | jq -r '.body' | jq .
```

### Test with AWS Console

1. Go to AWS Lambda Console
2. Select your function (`xbrl-validator`)
3. Go to "Test" tab
4. Create a new test event:
   - Event name: `test-with-dqc`
   - Event JSON: Copy from `lambda_examples/event_with_dqc.json`
5. Click "Test" button
6. Review execution results and logs

### Monitor CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/xbrl-validator --follow

# View recent logs
aws logs tail /aws/lambda/xbrl-validator --since 1h

# Filter for errors
aws logs filter-log-events \
    --log-group-name /aws/lambda/xbrl-validator \
    --filter-pattern "ERROR"
```

## 4. Integration Testing

### API Gateway Integration

If you've set up API Gateway:

```bash
# Test via HTTP endpoint
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/validate \
    -H "Content-Type: application/json" \
    -d '{
      "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
      "use_dqc_rules": true
    }'
```

### S3 Trigger Integration

If you've set up S3 trigger:

```bash
# Upload a test filing to S3
aws s3 cp test-filing.htm s3://your-filings-bucket/

# Check Lambda was triggered
aws logs tail /aws/lambda/xbrl-validator --follow

# Check validation results (if configured to write back to S3)
aws s3 ls s3://your-results-bucket/
```

## Expected Response Format

### Successful Validation

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json"
  },
  "body": "{
    \"status\": \"success\",
    \"filing_url\": \"https://www.sec.gov/...\",
    \"dqc_rules_enabled\": true,
    \"validation_output\": \"[info] Activation of plug-in Edgar Renderer successful...\\n[info] validated in 2.34 secs\",
    \"validation_errors\": null
  }"
}
```

### Error Response

```json
{
  "statusCode": 400,
  "body": "{
    \"status\": \"error\",
    \"message\": \"Missing required parameter: filing_url\"
  }"
}
```

## Performance Testing

### Measure Cold Start

```bash
# Invoke after function has been idle
time aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_with_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json
```

### Measure Warm Start

```bash
# Invoke immediately after previous invocation
time aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_with_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json
```

### Load Testing

Use a tool like `artillery` or `locust`:

```bash
# Install artillery
npm install -g artillery

# Create load test config
cat > load-test.yml << 'EOF'
config:
  target: "https://your-api-id.execute-api.us-east-1.amazonaws.com"
  phases:
    - duration: 60
      arrivalRate: 5
scenarios:
  - flow:
      - post:
          url: "/prod/validate"
          json:
            filing_url: "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm"
            use_dqc_rules: true
EOF

# Run load test
artillery run load-test.yml
```

## Troubleshooting Tests

### Container Won't Start

```bash
# Check container logs
docker logs <container-id>

# Run container with shell access
docker run -it --entrypoint /bin/bash xbrl-validator:latest

# Inside container, check Python
python3 --version
ls -la /var/task/
```

### Lambda Times Out

```bash
# Increase timeout
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --timeout 600

# Check CloudWatch metrics for duration
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Duration \
    --dimensions Name=FunctionName,Value=xbrl-validator \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average,Maximum
```

### Out of Memory

```bash
# Increase memory
aws lambda update-function-configuration \
    --function-name xbrl-validator \
    --memory-size 3008

# Check CloudWatch metrics for memory usage
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name MemoryUtilization \
    --dimensions Name=FunctionName,Value=xbrl-validator \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average,Maximum
```

### Validation Errors

If validation produces unexpected results:

1. **Test locally first**: Use `validate_filing.py` to verify the filing validates correctly
2. **Check plugin versions**: Ensure EDGAR and xule plugins are up to date
3. **Review logs**: Check CloudWatch logs for detailed error messages
4. **Compare outputs**: Run same filing locally and in Lambda, compare results

## Test Checklist

Before deploying to production:

- [ ] Syntax validation passes
- [ ] Docker image builds successfully
- [ ] Container runs locally
- [ ] Lambda function invokes successfully
- [ ] Validation output is correct
- [ ] Error handling works properly
- [ ] Performance is acceptable (< 300s for most filings)
- [ ] Memory usage is within limits (< 3GB)
- [ ] CloudWatch logs are readable
- [ ] Integration tests pass (if applicable)

## Continuous Testing

Set up automated testing:

```bash
# Create test script
cat > test_lambda.sh << 'EOF'
#!/bin/bash
set -e

echo "Testing Lambda function..."

# Invoke function
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://lambda_examples/event_with_dqc.json \
    --cli-binary-format raw-in-base64-out \
    response.json

# Check response
STATUS=$(cat response.json | jq -r '.statusCode')

if [ "$STATUS" = "200" ]; then
    echo "✓ Test passed"
    exit 0
else
    echo "✗ Test failed"
    cat response.json
    exit 1
fi
EOF

chmod +x test_lambda.sh

# Run test
./test_lambda.sh
```

## Resources

- [AWS Lambda Testing Documentation](https://docs.aws.amazon.com/lambda/latest/dg/testing-functions.html)
- [Lambda Runtime Interface Emulator](https://github.com/aws/aws-lambda-runtime-interface-emulator)
- [AWS CLI Lambda Commands](https://docs.aws.amazon.com/cli/latest/reference/lambda/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
