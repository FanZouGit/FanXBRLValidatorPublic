# XBRL Validator Frontend - Quick Start Guide

This is a quick start guide to get the React frontend up and running with AWS services.

## What You Get

A complete React web application that allows users to:
1. Upload XBRL/iXBRL files via drag-and-drop or file selection
2. Automatically upload to S3 and trigger Lambda validation
3. View validation results in real-time with categorized messages
4. Download results as JSON for further analysis

## Prerequisites

- AWS Account
- Node.js 18+
- Git

## Quick Setup (Local Development)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env.local` and fill in your AWS details:

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
VITE_AWS_REGION=us-east-1
VITE_S3_BUCKET_NAME=your-bucket-name
VITE_API_GATEWAY_ENDPOINT=https://your-api.execute-api.us-east-1.amazonaws.com/prod
```

### 3. Run Development Server

```bash
npm run dev
```

Visit `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## AWS Setup Required

Before the frontend will work, you need:

### 1. S3 Bucket
```bash
aws s3api create-bucket \
    --bucket your-xbrl-filings-bucket \
    --region us-east-1

# Enable CORS
aws s3api put-bucket-cors \
    --bucket your-xbrl-filings-bucket \
    --cors-configuration file://cors.json
```

CORS configuration (`cors.json`):
```json
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"]
    }
  ]
}
```

### 2. Lambda Function
Deploy the Lambda function as described in [AWS_LAMBDA_DEPLOYMENT.md](AWS_LAMBDA_DEPLOYMENT.md)

### 3. API Gateway
Create an API Gateway that triggers your Lambda function:
- POST method to `/validate`
- Enable CORS
- Configure Lambda proxy integration

### 4. Cognito Identity Pool (Optional)
For authenticated uploads, create a Cognito Identity Pool with S3 upload permissions.

## Deploy to AWS Amplify

### Quick Deploy

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click "New app" → "Host web app"
3. Connect your GitHub repository
4. Select branch to deploy
5. Add environment variables:
   - `VITE_AWS_REGION`
   - `VITE_S3_BUCKET_NAME`
   - `VITE_API_GATEWAY_ENDPOINT`
6. Click "Save and deploy"

Amplify will automatically:
- Detect the `amplify.yml` configuration
- Install dependencies
- Build the application
- Deploy to a CDN

Your app will be available at: `https://main.xxxxxx.amplifyapp.com`

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       v
┌──────────────────┐
│  AWS Amplify     │  (React Frontend)
│  - File Upload   │
│  - UI Display    │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│   Amazon S3      │  (File Storage)
└──────┬───────────┘
       │
       v
┌──────────────────┐
│  API Gateway     │  (REST API)
└──────┬───────────┘
       │
       v
┌──────────────────┐
│  AWS Lambda      │  (XBRL Validation)
│  - Arelle Engine │
│  - DQC Rules     │
└──────┬───────────┘
       │
       v
┌──────────────────┐
│   CloudWatch     │  (Logs & Monitoring)
└──────────────────┘
```

## File Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── FileUpload.jsx         # File upload with drag-and-drop
│   │   ├── ValidationResults.jsx  # Display validation results
│   ├── services/
│   │   └── s3Service.js          # S3 upload and Lambda trigger
│   ├── App.jsx                   # Main application
│   ├── aws-config.js             # AWS Amplify configuration
│   └── main.jsx                  # Application entry point
├── .env.example         # Environment template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
└── README.md           # Detailed documentation
```

## Troubleshooting

### Build Fails
- Verify Node.js version (18+)
- Delete `node_modules` and run `npm install` again
- Check for syntax errors with `npm run lint`

### Upload Fails
- Verify S3 bucket CORS configuration
- Check Cognito Identity Pool permissions
- Ensure API Gateway endpoint is correct
- Check browser console for detailed errors

### Validation Doesn't Trigger
- Verify Lambda function is deployed
- Check API Gateway configuration
- Review Lambda CloudWatch logs
- Test Lambda function directly

## Security Notes

⚠️ **Important Security Considerations:**

1. **Environment Variables**: Never commit `.env.local` with real credentials
2. **S3 Bucket Policies**: Use least-privilege access
3. **API Gateway**: Enable throttling and rate limiting
4. **CORS**: Restrict origins in production
5. **Authentication**: Consider adding Cognito authentication for production use

## Testing

### Run Linter
```bash
npm run lint
```

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Support

- **Frontend Issues**: See [frontend/README.md](frontend/README.md)
- **Deployment Issues**: See [FRONTEND_DEPLOYMENT.md](FRONTEND_DEPLOYMENT.md)
- **Lambda Issues**: See [AWS_LAMBDA_DEPLOYMENT.md](AWS_LAMBDA_DEPLOYMENT.md)
- **XBRL Validation**: See [README.md](README.md)

## Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [AWS SDK for JavaScript](https://docs.aws.amazon.com/sdk-for-javascript/)

## License

Apache License 2.0 (same as Arelle and plugins)
