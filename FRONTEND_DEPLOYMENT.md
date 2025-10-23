# Frontend Deployment Guide

Complete guide for deploying the XBRL Validator React frontend to AWS Amplify.

## Prerequisites

Before deploying, ensure you have:

- [x] AWS Account with appropriate permissions
- [x] Lambda function deployed (see [AWS_LAMBDA_DEPLOYMENT.md](AWS_LAMBDA_DEPLOYMENT.md))
- [x] S3 bucket created for file uploads
- [x] API Gateway endpoint configured (or S3 event trigger)
- [x] GitHub repository with the frontend code

## Architecture Overview

```
User → AWS Amplify (Frontend) → S3 Upload → Lambda Validation
                              ↓
                         API Gateway → Lambda
                              ↓
                         Results Display
```

## Step-by-Step Deployment

### Step 1: Create S3 Bucket for Uploads

```bash
# Create S3 bucket
aws s3api create-bucket \
    --bucket xbrl-validator-uploads \
    --region us-east-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
    --bucket xbrl-validator-uploads \
    --versioning-configuration Status=Enabled

# Configure CORS
cat > cors.json << 'EOF'
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
    --bucket xbrl-validator-uploads \
    --cors-configuration file://cors.json
```

### Step 2: Create API Gateway

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
    --name xbrl-validator-api \
    --description "API for XBRL validation" \
    --query 'id' \
    --output text)

echo "API ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query 'items[0].id' \
    --output text)

# Create /validate resource
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part validate \
    --query 'id' \
    --output text)

# Create POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE

# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name xbrl-validator \
    --query 'Configuration.FunctionArn' \
    --output text)

# Configure Lambda integration
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"

# Enable CORS
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}'

aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true, "method.response.header.Access-Control-Allow-Methods": true, "method.response.header.Access-Control-Allow-Origin": true}'

aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''", "method.response.header.Access-Control-Allow-Methods": "'\''POST,OPTIONS'\''", "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"}' \
    --response-templates '{"application/json": ""}'

# Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod

# Get API endpoint
echo "API Gateway Endpoint: https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
```

### Step 3: Create Cognito Identity Pool (Optional)

```bash
# Create identity pool
IDENTITY_POOL_ID=$(aws cognito-identity create-identity-pool \
    --identity-pool-name xbrl-validator-identity \
    --allow-unauthenticated-identities \
    --query 'IdentityPoolId' \
    --output text)

echo "Identity Pool ID: $IDENTITY_POOL_ID"

# Create IAM role for authenticated users
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "IDENTITY_POOL_ID"
        }
      }
    }
  ]
}
EOF

# Replace IDENTITY_POOL_ID in trust policy
sed -i "s/IDENTITY_POOL_ID/$IDENTITY_POOL_ID/g" trust-policy.json

# Create IAM role
ROLE_ARN=$(aws iam create-role \
    --role-name xbrl-validator-cognito-role \
    --assume-role-policy-document file://trust-policy.json \
    --query 'Role.Arn' \
    --output text)

# Attach policy for S3 upload
cat > s3-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::xbrl-validator-uploads/*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name xbrl-validator-cognito-role \
    --policy-name S3UploadPolicy \
    --policy-document file://s3-policy.json

# Set identity pool roles
aws cognito-identity set-identity-pool-roles \
    --identity-pool-id $IDENTITY_POOL_ID \
    --roles unauthenticated=$ROLE_ARN,authenticated=$ROLE_ARN
```

### Step 4: Deploy to AWS Amplify

#### Option A: Using AWS Console

1. **Go to AWS Amplify Console**:
   - Navigate to: https://console.aws.amazon.com/amplify/

2. **Create New App**:
   - Click "New app" → "Host web app"
   - Select "GitHub" as the source
   - Authorize AWS Amplify to access your repository
   - Select the repository: `FanZouGit/FanXBRLValidatorPublic`
   - Select the branch (e.g., `main`)

3. **Configure Build Settings**:
   - Amplify will auto-detect `amplify.yml`
   - Verify the build settings look correct
   - Click "Next"

4. **Add Environment Variables**:
   - Click "Advanced settings"
   - Add the following environment variables:
     ```
     VITE_AWS_REGION=us-east-1
     VITE_S3_BUCKET_NAME=xbrl-validator-uploads
     VITE_API_GATEWAY_ENDPOINT=https://[your-api-id].execute-api.us-east-1.amazonaws.com/prod
     VITE_IDENTITY_POOL_ID=[your-identity-pool-id]
     ```

5. **Deploy**:
   - Click "Save and deploy"
   - Wait for deployment to complete (5-10 minutes)

6. **Access Your App**:
   - Once deployed, you'll get a URL like: `https://main.xxxxxx.amplifyapp.com`

#### Option B: Using AWS CLI

```bash
# Create Amplify app
APP_ID=$(aws amplify create-app \
    --name xbrl-validator \
    --repository https://github.com/FanZouGit/FanXBRLValidatorPublic \
    --oauth-token YOUR_GITHUB_TOKEN \
    --query 'app.appId' \
    --output text)

echo "App ID: $APP_ID"

# Create branch
aws amplify create-branch \
    --app-id $APP_ID \
    --branch-name main

# Set environment variables
aws amplify update-app \
    --app-id $APP_ID \
    --environment-variables \
        VITE_AWS_REGION=us-east-1 \
        VITE_S3_BUCKET_NAME=xbrl-validator-uploads \
        VITE_API_GATEWAY_ENDPOINT=https://[your-api-id].execute-api.us-east-1.amazonaws.com/prod \
        VITE_IDENTITY_POOL_ID=[your-identity-pool-id]

# Start deployment
aws amplify start-job \
    --app-id $APP_ID \
    --branch-name main \
    --job-type RELEASE
```

### Step 5: Configure Custom Domain (Optional)

```bash
# Add custom domain
aws amplify create-domain-association \
    --app-id $APP_ID \
    --domain-name xbrl-validator.example.com \
    --sub-domain-settings prefix=www,branchName=main

# Wait for DNS verification
aws amplify get-domain-association \
    --app-id $APP_ID \
    --domain-name xbrl-validator.example.com
```

## Post-Deployment Configuration

### 1. Test the Application

1. Open the Amplify app URL
2. Try uploading a sample XBRL file
3. Verify validation results are displayed
4. Check Lambda CloudWatch logs for any errors

### 2. Monitor Usage

```bash
# View Amplify app metrics
aws amplify get-app --app-id $APP_ID

# View Lambda metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=xbrl-validator \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-12-31T23:59:59Z \
    --period 3600 \
    --statistics Sum
```

### 3. Set Up Alarms

```bash
# Create CloudWatch alarm for Lambda errors
aws cloudwatch put-metric-alarm \
    --alarm-name xbrl-validator-errors \
    --alarm-description "Alert on Lambda errors" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --dimensions Name=FunctionName,Value=xbrl-validator \
    --evaluation-periods 1
```

## Continuous Deployment

Amplify automatically deploys when you push to the connected branch.

To manually trigger a deployment:

```bash
aws amplify start-job \
    --app-id $APP_ID \
    --branch-name main \
    --job-type RELEASE
```

## Updating Environment Variables

```bash
# Update environment variables
aws amplify update-app \
    --app-id $APP_ID \
    --environment-variables \
        VITE_AWS_REGION=us-east-1 \
        VITE_S3_BUCKET_NAME=new-bucket-name

# Redeploy to apply changes
aws amplify start-job \
    --app-id $APP_ID \
    --branch-name main \
    --job-type RELEASE
```

## Troubleshooting

### Build Fails

1. Check build logs in Amplify Console
2. Verify `amplify.yml` is in repository root
3. Ensure `frontend/package.json` exists
4. Check for syntax errors in code

### Upload Fails

1. Verify S3 bucket CORS configuration
2. Check Cognito Identity Pool IAM roles
3. Verify S3 bucket name in environment variables
4. Check browser console for errors

### Validation Doesn't Work

1. Check API Gateway endpoint is correct
2. Verify Lambda function is deployed
3. Check Lambda CloudWatch logs
4. Test Lambda directly with AWS CLI
5. Verify API Gateway CORS configuration

### CORS Errors

1. Update S3 bucket CORS:
   ```bash
   aws s3api put-bucket-cors \
       --bucket xbrl-validator-uploads \
       --cors-configuration file://cors.json
   ```

2. Update API Gateway CORS (see Step 2 above)

## Security Best Practices

1. **Use HTTPS Only**: Amplify enforces HTTPS automatically
2. **Limit S3 Bucket Access**: Use least-privilege IAM policies
3. **Enable CloudWatch Logs**: Monitor all API and Lambda activity
4. **Set Up WAF**: Add AWS WAF rules to API Gateway
5. **Implement Rate Limiting**: Use API Gateway throttling
6. **Regular Security Audits**: Review IAM permissions quarterly

## Cost Optimization

1. **S3 Lifecycle Policies**: Delete old uploads after 30 days
2. **Lambda Reserved Concurrency**: Prevent runaway costs
3. **CloudWatch Log Retention**: Set to 7 days for non-production
4. **Amplify Build Minutes**: Use manual deployments when possible

## Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [S3 Documentation](https://docs.aws.amazon.com/s3/)

## Support

For deployment issues:
- Check AWS CloudWatch logs
- Review Amplify build logs
- Contact AWS Support
- Open an issue on GitHub repository
