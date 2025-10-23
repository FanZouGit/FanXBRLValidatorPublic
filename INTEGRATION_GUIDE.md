# Frontend-Backend Integration Guide

This document explains how the React frontend integrates with the AWS Lambda backend for XBRL validation.

## Integration Flow

### 1. File Upload to S3

```javascript
// In src/services/s3Service.js
import { uploadData } from 'aws-amplify/storage'

// User selects file
const file = selectedFile // File object from input

// Upload to S3 with progress tracking
const result = await uploadData({
  path: `uploads/${timestamp}-${file.name}`,
  data: file,
  options: {
    onProgress: ({ transferredBytes, totalBytes }) => {
      // Update progress bar
      const percentage = (transferredBytes / totalBytes) * 100
      updateProgress(percentage)
    }
  }
}).result
```

### 2. Trigger Lambda via API Gateway

```javascript
import { post } from 'aws-amplify/api'

// After successful upload, trigger validation
const response = await post({
  apiName: 'xbrlValidatorApi',
  path: '/validate',
  options: {
    body: {
      filing_url: `s3://bucket-name/${s3Key}`,
      use_dqc_rules: true
    }
  }
}).response
```

### 3. Lambda Processing

The Lambda function receives the request:

```python
# lambda_handler.py
def lambda_handler(event, context):
    filing_url = event['filing_url']  # S3 path or HTTP URL
    use_dqc_rules = event.get('use_dqc_rules', True)
    
    # Validate using Arelle
    success, output, error = validate_filing(filing_url, use_dqc_rules)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'success' if success else 'error',
            'filing_url': filing_url,
            'validation_output': output,
            'validation_errors': error
        })
    }
```

### 4. Display Results

```javascript
// In ValidationResults.jsx
function ValidationResults({ results }) {
  const { status, validation_output } = results
  
  // Parse and categorize messages
  const messages = parseValidationOutput(validation_output)
  
  // Display:
  // - Errors (EFM rules)
  // - DQC violations
  // - Warnings
  // - Info messages
}
```

## Integration Options

### Option 1: API Gateway (Recommended)

**Pros:**
- Full control over request/response
- Synchronous validation with immediate results
- Easy error handling
- Can add authentication, rate limiting, etc.

**Setup:**
1. Create API Gateway REST API
2. Add POST method to `/validate`
3. Configure Lambda proxy integration
4. Enable CORS
5. Deploy to stage (e.g., 'prod')

**Configuration:**
```env
VITE_API_GATEWAY_ENDPOINT=https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

### Option 2: S3 Event Trigger

**Pros:**
- Simpler setup (no API Gateway needed)
- Automatic triggering on upload
- Lower cost

**Cons:**
- Asynchronous (need polling or WebSocket for results)
- Less control over request flow

**Setup:**
1. Configure S3 bucket notification
2. Trigger Lambda on s3:ObjectCreated:*
3. Store results in S3 or DynamoDB
4. Frontend polls for results

## API Gateway Configuration

### CORS Configuration

API Gateway needs CORS enabled for browser requests:

```json
{
  "AllowOrigins": ["*"],
  "AllowMethods": ["POST", "OPTIONS"],
  "AllowHeaders": ["Content-Type", "X-Amz-Date", "Authorization"]
}
```

### Request Format

```json
{
  "filing_url": "s3://bucket-name/path/to/file.htm",
  "use_dqc_rules": true
}
```

Or with HTTP URL:
```json
{
  "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
  "use_dqc_rules": true
}
```

### Response Format

```json
{
  "statusCode": 200,
  "body": {
    "status": "success",
    "filing_url": "s3://bucket-name/path/to/file.htm",
    "dqc_rules_enabled": true,
    "validation_output": "[info] Validation successful\n[EFM.6.05.20] Issue found...",
    "validation_errors": null
  }
}
```

## S3 Configuration

### Bucket Policy

Allow Cognito users to upload:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*",
      "Condition": {
        "StringLike": {
          "cognito-identity.amazonaws.com:sub": "*"
        }
      }
    }
  ]
}
```

### CORS Configuration

```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

### Lifecycle Policy (Optional)

Auto-delete old uploads after 30 days:

```json
{
  "Rules": [
    {
      "Id": "DeleteOldUploads",
      "Status": "Enabled",
      "Prefix": "uploads/",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

## Cognito Configuration

### Identity Pool

Create an identity pool for unauthenticated access:

```bash
aws cognito-identity create-identity-pool \
    --identity-pool-name xbrl-validator \
    --allow-unauthenticated-identities
```

### IAM Roles

Unauthenticated role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/uploads/*"
    },
    {
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:us-east-1:*:*/*/POST/validate"
    }
  ]
}
```

## Error Handling

### Frontend Error Handling

```javascript
try {
  const result = await uploadToS3(file, useDqcRules, onProgress)
  onValidationComplete(result)
} catch (error) {
  if (error.code === 'NoSuchBucket') {
    setError('S3 bucket not found. Please check configuration.')
  } else if (error.code === 'AccessDenied') {
    setError('Access denied. Please check IAM permissions.')
  } else if (error.name === 'NetworkError') {
    setError('Network error. Please check your connection.')
  } else {
    setError(`Upload failed: ${error.message}`)
  }
}
```

### Lambda Error Responses

```python
# Handle validation errors
try:
    success, output, error = validate_filing(filing_url, use_dqc_rules)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'success',
            'validation_output': output
        })
    }
except Exception as e:
    return {
        'statusCode': 500,
        'body': json.dumps({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        })
    }
```

## Testing Integration

### Test S3 Upload

```bash
# Upload a test file
aws s3 cp test-filing.htm s3://your-bucket/uploads/test-filing.htm

# Verify upload
aws s3 ls s3://your-bucket/uploads/
```

### Test API Gateway

```bash
# Test validation endpoint
curl -X POST \
  https://your-api.execute-api.us-east-1.amazonaws.com/prod/validate \
  -H 'Content-Type: application/json' \
  -d '{
    "filing_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm",
    "use_dqc_rules": true
  }'
```

### Test Lambda Directly

```bash
aws lambda invoke \
    --function-name xbrl-validator \
    --payload file://test-event.json \
    response.json

cat response.json | jq .
```

## Monitoring

### CloudWatch Metrics

Monitor:
- API Gateway request count
- Lambda invocations
- Lambda errors
- Lambda duration
- S3 PUT requests

### CloudWatch Logs

- Frontend errors (browser console)
- API Gateway access logs
- Lambda execution logs
- S3 access logs (if enabled)

### CloudWatch Alarms

Set up alarms for:
- Lambda error rate > 5%
- Lambda duration > 5 minutes
- API Gateway 4xx/5xx errors
- S3 upload failures

## Security Best Practices

1. **HTTPS Only**: Amplify enforces HTTPS automatically
2. **Input Validation**: Validate file types and sizes on frontend and backend
3. **Rate Limiting**: Use API Gateway throttling
4. **Authentication**: Add Cognito authentication for production
5. **Bucket Policies**: Use least-privilege access
6. **Environment Variables**: Never commit secrets to git
7. **CORS**: Restrict origins in production

## Performance Optimization

1. **Lambda Memory**: Allocate 2048MB or more for complex filings
2. **Lambda Timeout**: Set to 300 seconds (5 minutes) or higher
3. **S3 Transfer Acceleration**: Enable for faster uploads
4. **CloudFront**: Use CloudFront CDN for frontend (automatic with Amplify)
5. **Concurrent Executions**: Set reserved concurrency to prevent throttling

## Troubleshooting Common Issues

### CORS Errors
- Verify S3 bucket CORS configuration
- Check API Gateway CORS settings
- Ensure Lambda returns proper CORS headers

### Upload Timeout
- Increase file size limit
- Check network connection
- Verify S3 bucket region matches configuration

### Validation Fails
- Check Lambda CloudWatch logs
- Verify filing URL is accessible
- Test Lambda function directly
- Check Lambda execution role permissions

### Results Not Displayed
- Check browser console for errors
- Verify API response format
- Test API endpoint with curl
- Check JSON parsing in frontend

## Resources

- [AWS Amplify Storage](https://docs.amplify.aws/lib/storage/getting-started/q/platform/js/)
- [AWS Amplify API](https://docs.amplify.aws/lib/restapi/getting-started/q/platform/js/)
- [API Gateway CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html)
- [S3 CORS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html)
- [Lambda Error Handling](https://docs.aws.amazon.com/lambda/latest/dg/python-exceptions.html)
