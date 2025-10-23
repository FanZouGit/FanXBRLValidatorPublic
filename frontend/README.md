# XBRL Validator Frontend

React-based web application for uploading EDGAR XBRL and iXBRL filings to AWS S3, triggering Lambda validation, and displaying results.

## Features

- 📤 **Drag & Drop Upload**: Easy file upload interface with drag-and-drop support
- ☁️ **AWS S3 Integration**: Direct upload to S3 bucket
- ⚡ **Lambda Validation**: Automatic triggering of XBRL validation via AWS Lambda
- ✅ **Real-time Results**: Display validation results with categorized messages
- 📊 **DQC Rules Support**: Optional Data Quality Committee rule validation
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🌙 **Dark/Light Mode**: Automatic theme based on system preferences

## Prerequisites

- Node.js 18+ and npm
- AWS Account with:
  - S3 bucket for file uploads
  - Lambda function for XBRL validation (see [AWS_LAMBDA_DEPLOYMENT.md](../AWS_LAMBDA_DEPLOYMENT.md))
  - API Gateway endpoint (or S3 event trigger)
  - Cognito (optional, for authentication)

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Copy the example environment file and configure your AWS settings:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your AWS configuration:

```env
VITE_AWS_REGION=us-east-1
VITE_S3_BUCKET_NAME=your-xbrl-filings-bucket
VITE_API_GATEWAY_ENDPOINT=https://your-api-id.execute-api.us-east-1.amazonaws.com/prod

# Optional: AWS Cognito for authentication
VITE_USER_POOL_ID=us-east-1_xxxxxxxxx
VITE_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
VITE_IDENTITY_POOL_ID=us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 3. Run Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
```

The production build will be created in the `dist` directory.

## AWS Setup

### Option 1: API Gateway Integration

This is the recommended approach for full control over the validation flow.

1. **Create API Gateway REST API**:
   ```bash
   aws apigateway create-rest-api --name xbrl-validator-api
   ```

2. **Create Lambda Integration**:
   - Link API Gateway to your Lambda function
   - Set up POST method on `/validate` endpoint
   - Configure CORS settings

3. **Update Environment Variables**:
   - Set `VITE_API_GATEWAY_ENDPOINT` to your API Gateway URL

### Option 2: S3 Event Trigger

Alternative approach where S3 automatically triggers Lambda on file upload.

1. **Configure S3 Bucket Notification**:
   ```bash
   aws s3api put-bucket-notification-configuration \
     --bucket your-xbrl-filings-bucket \
     --notification-configuration file://notification.json
   ```

2. **Use S3 Trigger Method**:
   - Modify `src/services/s3Service.js` to use `uploadWithS3Trigger`
   - Implement polling or WebSocket for results

### AWS Cognito Setup (Optional)

For authenticated uploads:

1. **Create Cognito User Pool**:
   ```bash
   aws cognito-idp create-user-pool --pool-name xbrl-validator-users
   ```

2. **Create Identity Pool**:
   ```bash
   aws cognito-identity create-identity-pool \
     --identity-pool-name xbrl-validator-identity \
     --allow-unauthenticated-identities
   ```

3. **Configure IAM Roles**:
   - Grant S3 upload permissions
   - Grant Lambda invoke permissions (if using direct invocation)

## Deployment to AWS Amplify

### 1. Connect Repository

1. Go to AWS Amplify Console
2. Click "New app" → "Host web app"
3. Connect your GitHub repository
4. Select the branch to deploy

### 2. Configure Build Settings

Amplify will automatically detect the `amplify.yml` configuration file at the root of the repository.

The build configuration includes:
```yaml
frontend:
  phases:
    preBuild:
      - cd frontend && npm ci
    build:
      - npm run build
  artifacts:
    baseDirectory: frontend/dist
```

### 3. Set Environment Variables

In Amplify Console, add the following environment variables:

- `VITE_AWS_REGION`
- `VITE_S3_BUCKET_NAME`
- `VITE_API_GATEWAY_ENDPOINT`
- `VITE_USER_POOL_ID` (if using Cognito)
- `VITE_USER_POOL_CLIENT_ID` (if using Cognito)
- `VITE_IDENTITY_POOL_ID` (if using Cognito)

### 4. Deploy

Click "Save and deploy" to trigger the first deployment.

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── FileUpload.jsx
│   │   ├── FileUpload.css
│   │   ├── ValidationResults.jsx
│   │   └── ValidationResults.css
│   ├── services/        # Service layer
│   │   └── s3Service.js
│   ├── App.jsx          # Main app component
│   ├── App.css
│   ├── main.jsx         # Entry point
│   ├── index.css        # Global styles
│   └── aws-config.js    # AWS Amplify configuration
├── .env.example         # Example environment variables
├── .env.local           # Local environment variables (git-ignored)
├── index.html           # HTML template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
└── README.md            # This file
```

## Usage

1. **Select File**: Click "Select File" or drag and drop an XBRL/iXBRL file
2. **Configure Options**: Choose whether to enable DQC rules
3. **Upload**: Click "Upload and Validate"
4. **View Results**: See validation results categorized by type:
   - Errors (EFM rules)
   - DQC Rule Violations
   - Warnings
   - Information Messages
5. **Download Results**: Export results as JSON for further analysis

## Supported File Types

- `.htm` - iXBRL HTML files
- `.html` - iXBRL HTML files
- `.xbrl` - XBRL instance documents
- `.xml` - XBRL XML files

Maximum file size: 50MB

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Technology Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **AWS Amplify** - AWS SDK integration
- **CSS3** - Styling with CSS variables

## Troubleshooting

### CORS Errors

If you encounter CORS errors when uploading to S3:

1. Configure S3 bucket CORS policy:
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```

2. Configure API Gateway CORS if using API Gateway integration

### Upload Fails

- Verify S3 bucket name and region in `.env.local`
- Check IAM permissions for Cognito Identity Pool
- Ensure Lambda function has correct permissions
- Check browser console for detailed error messages

### Validation Not Triggering

- Verify API Gateway endpoint is correct
- Check Lambda function logs in CloudWatch
- Ensure Lambda execution role has necessary permissions
- Test Lambda function directly with AWS CLI

## Security Considerations

- Never commit `.env.local` with real credentials
- Use Cognito for production authentication
- Implement rate limiting on API Gateway
- Set appropriate S3 bucket policies
- Enable CloudWatch logging for audit trails
- Use HTTPS only (enforced by Amplify)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project uses Arelle and its plugins, which are licensed under Apache License 2.0.

## Support

For issues related to:
- **Frontend**: Open an issue on this repository
- **Backend/Lambda**: See [AWS_LAMBDA_DEPLOYMENT.md](../AWS_LAMBDA_DEPLOYMENT.md)
- **XBRL Validation**: See main [README.md](../README.md)
