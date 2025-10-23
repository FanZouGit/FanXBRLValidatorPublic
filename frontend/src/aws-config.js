import { Amplify } from 'aws-amplify'

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_USER_POOL_CLIENT_ID,
      identityPoolId: import.meta.env.VITE_IDENTITY_POOL_ID,
      loginWith: {
        email: true,
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: true,
        },
      },
      allowGuestAccess: true,
    },
  },
  Storage: {
    S3: {
      bucket: import.meta.env.VITE_S3_BUCKET_NAME,
      region: import.meta.env.VITE_AWS_REGION,
    },
  },
  API: {
    REST: {
      xbrlValidatorApi: {
        endpoint: import.meta.env.VITE_API_GATEWAY_ENDPOINT,
        region: import.meta.env.VITE_AWS_REGION,
      },
    },
  },
}

// Configure Amplify
Amplify.configure(amplifyConfig)

export default amplifyConfig
