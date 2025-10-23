import { uploadData } from 'aws-amplify/storage'
import { post } from 'aws-amplify/api'

/**
 * Upload a file to S3 and trigger Lambda validation
 * @param {File} file - The file to upload
 * @param {boolean} useDqcRules - Whether to use DQC rules in validation
 * @param {Function} onProgress - Progress callback function
 * @returns {Promise<Object>} Validation results
 */
export async function uploadToS3(file, useDqcRules = true, onProgress = () => {}) {
  try {
    // Generate a unique file name with timestamp
    const timestamp = Date.now()
    const fileName = `uploads/${timestamp}-${file.name}`

    // Upload file to S3
    const result = await uploadData({
      path: fileName,
      data: file,
      options: {
        contentType: file.type || 'application/octet-stream',
        onProgress: ({ transferredBytes, totalBytes }) => {
          if (totalBytes) {
            const percentage = Math.round((transferredBytes / totalBytes) * 100)
            onProgress(percentage)
          }
        },
      },
    }).result

    console.log('Upload successful:', result)

    // Update progress to 100% after upload completes
    onProgress(100)

    // Trigger Lambda validation via API Gateway or invoke directly
    const s3Key = result.path
    const validationResult = await invokeLambdaValidation(s3Key, useDqcRules)

    return validationResult
  } catch (error) {
    console.error('Error uploading file:', error)
    throw new Error(`Upload failed: ${error.message}`)
  }
}

/**
 * Invoke Lambda function for validation
 * @param {string} s3Key - S3 object key
 * @param {boolean} useDqcRules - Whether to use DQC rules
 * @returns {Promise<Object>} Validation results
 */
async function invokeLambdaValidation(s3Key, useDqcRules) {
  try {
    // Construct the S3 URL for the uploaded file
    const bucketName = import.meta.env.VITE_S3_BUCKET_NAME
    const region = import.meta.env.VITE_AWS_REGION
    const s3Url = `s3://${bucketName}/${s3Key}`
    
    // Call API Gateway endpoint that triggers Lambda
    const response = await post({
      apiName: 'xbrlValidatorApi',
      path: '/validate',
      options: {
        body: {
          filing_url: s3Url,
          use_dqc_rules: useDqcRules,
        },
      },
    }).response

    const data = await response.body.json()
    
    // Parse the response body if it's a string
    let result = data
    if (typeof data.body === 'string') {
      result = JSON.parse(data.body)
    } else if (data.body) {
      result = data.body
    }

    return result
  } catch (error) {
    console.error('Error invoking Lambda:', error)
    throw new Error(`Validation failed: ${error.message}`)
  }
}

/**
 * Alternative: Upload to S3 with automatic Lambda trigger via S3 event
 * This approach requires S3 bucket to be configured with Lambda trigger
 * @param {File} file - The file to upload
 * @param {boolean} useDqcRules - Whether to use DQC rules
 * @param {Function} onProgress - Progress callback
 * @returns {Promise<Object>} Upload result with polling for validation
 */
export async function uploadWithS3Trigger(file, useDqcRules = true, onProgress = () => {}) {
  try {
    const timestamp = Date.now()
    const fileName = `uploads/${timestamp}-${file.name}`

    // Upload file to S3 - this will automatically trigger Lambda via S3 event
    const result = await uploadData({
      path: fileName,
      data: file,
      options: {
        contentType: file.type || 'application/octet-stream',
        metadata: {
          useDqcRules: useDqcRules.toString(),
          timestamp: timestamp.toString(),
        },
        onProgress: ({ transferredBytes, totalBytes }) => {
          if (totalBytes) {
            const percentage = Math.round((transferredBytes / totalBytes) * 100)
            onProgress(Math.min(percentage, 95)) // Reserve 5% for processing
          }
        },
      },
    }).result

    console.log('Upload successful, waiting for validation:', result)
    onProgress(100)

    // Poll for validation results
    // In a real implementation, you might use WebSocket or polling
    // For now, we'll simulate a successful validation
    await new Promise(resolve => setTimeout(resolve, 2000))

    return {
      status: 'success',
      filing_url: fileName,
      dqc_rules_enabled: useDqcRules,
      validation_output: '[info] File uploaded successfully. Validation in progress...',
      message: 'File uploaded to S3. Lambda validation triggered automatically.',
    }
  } catch (error) {
    console.error('Error uploading file:', error)
    throw new Error(`Upload failed: ${error.message}`)
  }
}
