# Copilot Instructions for XBRL Validator

## Repository Overview

This repository contains a comprehensive XBRL validation solution for SEC EDGAR filings. The project uses **Arelle** as the core validation engine with integrated EDGAR and XULE plugins for SEC-specific validation rules and Data Quality Committee (DQC) checks.

**Key Components:**
- **Python Backend**: Core validation logic using Arelle engine
- **React Frontend**: Web interface for uploading and validating filings (Vite + React 18)
- **AWS Lambda**: Serverless validation function for scalable processing
- **AWS Integrations**: DynamoDB (storage), SQS (queuing), SNS (notifications)

## Architecture

```
Filing Upload (Web/CLI)
    ↓
Validation Engine (Arelle + EDGAR/render + xule plugins)
    ↓
EFM Rules + DQCRT/DQC Checks (automatic based on taxonomy version)
    ↓
Results → DynamoDB (optional) → SQS (optional) → SNS (optional)
```

## Technology Stack

### Backend (Python)
- **Python 3.8+** (tested on 3.12)
- **Arelle**: XBRL validation engine (submodule in `Arelle/` directory)
- **Key Dependencies**: lxml, boto3, requests, numpy, openpyxl (see `requirements-lambda.txt`)
- **Testing**: Simple Python test functions (no framework like pytest/unittest)

### Frontend (React)
- **React 18** with Vite build tool
- **AWS Amplify** SDK for AWS integrations
- **Location**: `frontend/` directory
- **Build**: `npm run build` (uses Vite)
- **Dev Server**: `npm run dev`
- **Linting**: ESLint with React plugins

### AWS Services
- **Lambda**: Container-based deployment (see `Dockerfile.lambda`)
- **DynamoDB**: Validation results storage
- **S3**: Frontend hosting via Amplify
- **SQS**: Queue for successful validations
- **SNS**: Email/SMS notifications for failures

## Code Structure

### Core Files
- `validate_filing.py`: CLI validator script with EFM and DQC validation
- `lambda_handler.py`: AWS Lambda entry point for serverless validation
- `dynamodb_helper.py`: DynamoDB integration utilities
- `sns_helper.py`: SNS notification utilities
- `sqs_helper.py`: SQS queue utilities
- `setup_plugins.sh`: Automated setup for EDGAR and xule plugins

### Test Files
- `test_dynamodb_helper.py`: DynamoDB helper tests
- `test_sns_helper.py`: SNS helper tests
- `test_sqs_helper.py`: SQS helper tests

**Note**: Tests are simple Python scripts with test functions, not pytest/unittest. They can be run directly with `python test_*.py`.

### Frontend Structure
```
frontend/
├── src/
│   ├── components/    # React components
│   ├── App.jsx        # Main application
│   └── main.jsx       # Entry point
├── package.json       # NPM dependencies
├── vite.config.js     # Vite configuration
└── .eslintrc.cjs      # ESLint configuration
```

### Documentation
- `README.md`: Main documentation with setup and usage
- `QUICKSTART.md`: Quick start guide
- `AWS_LAMBDA_DEPLOYMENT.md`: Lambda deployment instructions
- `FRONTEND_DEPLOYMENT.md`: Frontend deployment to AWS Amplify
- `FRONTEND_QUICKSTART.md`: Frontend development quickstart
- `DYNAMODB_SCHEMA.md`: DynamoDB table schema
- `INTEGRATION_GUIDE.md`: Integration patterns
- `IMPLEMENTATION_NOTES.md` & `IMPLEMENTATION_SUMMARY.md`: Technical details

## Development Guidelines

### Python Code Conventions
- **Style**: Follow PEP 8 conventions
- **Imports**: Standard library → Third-party → Local imports (separated by blank lines)
- **Comments**: Use docstrings for functions and classes
- **Error Handling**: Use try-except blocks for AWS operations and external dependencies
- **User Agent**: Always use informative HTTP user agent for SEC requests

### Frontend Code Conventions
- **Style**: Follow ESLint rules defined in `.eslintrc.cjs`
- **Components**: Functional components with hooks (no class components)
- **State Management**: React hooks (useState, useEffect)
- **File Extensions**: Use `.jsx` for components with JSX

### Validation Logic
- **EDGAR Plugin**: Always use `EDGAR/render` plugin (includes built-in DQCRT/DQC support)
- **XULE Plugin**: Required by EDGAR plugin for rule execution (must be installed)
- **DQC Rules**: Automatically applied based on taxonomy version:
  - `us-gaap/2025+`: XULE-based DQCRT rules
  - `us-gaap/2023-2024`: Python-based DQC rules
- **Disabling DQC**: Use `--parameters dqcRuleFilter=(?!)` to disable DQC rules

### AWS Integration
- **Environment Variables**: 
  - `AWS_DEFAULT_REGION`: AWS region for services
  - `DYNAMODB_TABLE_NAME`: DynamoDB table name (optional)
  - `SQS_QUEUE_URL`: SQS queue URL (optional)
  - `SNS_TOPIC_ARN`: SNS topic ARN (optional)
- **Graceful Degradation**: AWS services are optional; code should work without them
- **Error Handling**: Catch and log boto3 exceptions, don't fail validation

## Building and Testing

### Python Backend

**Install Dependencies:**
```bash
cd Arelle
pip install -r requirements.txt
cd ..
```

**Setup Plugins (Required):**
```bash
./setup_plugins.sh
```
This clones EDGAR and xule plugins into `Arelle/arelle/plugin/`

**Run Validation:**
```bash
# With DQC rules (default)
python validate_filing.py <filing-url>

# Without DQC rules
python validate_filing.py <filing-url> --no-dqc
```

**Run Tests:**
```bash
# Run individual test files
python test_dynamodb_helper.py
python test_sns_helper.py
python test_sqs_helper.py
```

### Frontend

**Install Dependencies:**
```bash
cd frontend
npm install
```

**Development Server:**
```bash
npm run dev
```

**Build:**
```bash
npm run build
```

**Lint:**
```bash
npm run lint
```

### Lambda Deployment

**Build Container:**
```bash
docker build -f Dockerfile.lambda -t xbrl-validator:latest .
```

See `AWS_LAMBDA_DEPLOYMENT.md` for complete deployment instructions.

## Important Notes for Copilot

### Plugin System
- The project uses Arelle's plugin system extensively
- **EDGAR plugin**: Contains SEC-specific validation rules
- **xule plugin**: Rule engine for DQC/DQCRT validation
- Plugins must be cloned into `Arelle/arelle/plugin/` directory
- DO NOT remove or modify plugin setup logic

### Arelle Submodule
- `Arelle/` is a Git submodule pointing to the Arelle project
- Avoid modifying core Arelle code
- External plugins (EDGAR, xule) are cloned at setup time

### AWS Services are Optional
- All AWS integrations (DynamoDB, SQS, SNS) are optional
- Code should function without AWS credentials
- Use try-except blocks to handle missing boto3 or credentials gracefully

### Validation Workflow
- The core workflow is: Upload → Validate → Store (optional) → Queue (optional) → Notify (optional)
- Validation is the primary function; storage and notifications are enhancements
- Always maintain the ability to run validation locally without AWS

### DQC/DQCRT Rules
- DQC rules are part of the EDGAR plugin (not a separate plugin)
- Rules are automatically selected based on the filing's taxonomy version
- The `dqcRuleFilter` parameter controls which rules execute
- Default behavior includes DQC rules; they must be explicitly disabled

### Testing
- Tests are simple Python scripts, not pytest/unittest based
- Tests require AWS credentials to run fully
- Tests may be skipped if boto3 is unavailable (graceful degradation)
- Frontend tests follow Jest/React Testing Library patterns (if added)

### Security Considerations
- Never commit AWS credentials or secrets
- Use environment variables for sensitive configuration
- The `.env.example` file shows required variables
- Lambda uses IAM roles, not hardcoded credentials

### Performance
- Large filings may require increased memory limits
- Lambda function requires sufficient memory (recommend 2GB+)
- Arelle caching helps with repeated schema downloads
- Network timeouts may occur for remote filing validation

## Common Tasks

### Adding a New Python Helper Module
1. Create module in root directory (e.g., `new_helper.py`)
2. Add corresponding test file (e.g., `test_new_helper.py`)
3. Import in `lambda_handler.py` if used in Lambda
4. Add dependencies to `requirements-lambda.txt` if needed
5. Update README.md with usage instructions

### Modifying Validation Logic
1. Edit `validate_filing.py` or create new validation functions
2. Test with sample filings (local or remote URLs)
3. Verify both with and without DQC rules
4. Update `lambda_handler.py` if changes affect Lambda
5. Document changes in appropriate .md files

### Adding Frontend Features
1. Create components in `frontend/src/components/`
2. Follow existing component patterns (functional + hooks)
3. Run `npm run lint` to check code style
4. Test with `npm run dev` locally
5. Build with `npm run build` to verify production build

### Updating Dependencies
- **Python**: Update `requirements-lambda.txt` and test Lambda build
- **Frontend**: Update `frontend/package.json` and rebuild
- **Arelle**: Update submodule reference (advanced, usually not needed)

## Resources

- [Arelle Documentation](https://arelle.readthedocs.io/)
- [EDGAR Plugin](https://github.com/Arelle/EDGAR)
- [XULE Plugin](https://github.com/xbrlus/xule)
- [DQC Rules](https://xbrl.us/dqc-rules/)
- [SEC EDGAR System](https://www.sec.gov/edgar)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

## Questions to Ask Before Making Changes

1. **Does this change affect validation logic?** → Test with real filings
2. **Does this add new dependencies?** → Update requirements files and Docker image
3. **Does this modify AWS integrations?** → Ensure graceful degradation without AWS
4. **Does this change the plugin system?** → Verify plugins still load correctly
5. **Does this affect Lambda?** → Test Docker build and memory requirements
6. **Does this modify the frontend?** → Run ESLint and test build process
7. **Are tests needed?** → Add simple test files following existing patterns
