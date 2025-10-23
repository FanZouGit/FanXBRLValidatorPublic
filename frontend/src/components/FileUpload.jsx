import { useState, useRef } from 'react'
import { uploadToS3 } from '../services/s3Service'
import './FileUpload.css'

function FileUpload({ onValidationStart, onValidationComplete, isValidating }) {
  const [selectedFile, setSelectedFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [useDqcRules, setUseDqcRules] = useState(true)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (file) => {
    const validExtensions = ['.htm', '.html', '.xbrl', '.xml']
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
    
    if (!validExtensions.includes(fileExtension)) {
      setError(`Invalid file type. Please upload an XBRL file (${validExtensions.join(', ')})`)
      setSelectedFile(null)
      return
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      setError('File size exceeds 50MB limit')
      setSelectedFile(null)
      return
    }

    setError(null)
    setSelectedFile(file)
  }

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first')
      return
    }

    setError(null)
    onValidationStart()
    setUploadProgress(0)

    try {
      // Upload to S3 and trigger Lambda validation
      const result = await uploadToS3(
        selectedFile, 
        useDqcRules,
        (progress) => {
          setUploadProgress(progress)
        }
      )

      onValidationComplete(result)
      setSelectedFile(null)
      setUploadProgress(0)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError(err.message || 'Failed to upload and validate file')
      onValidationComplete(null)
    }
  }

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="file-upload-container">
      <div 
        className={`drop-zone ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".htm,.html,.xbrl,.xml"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
          disabled={isValidating}
        />

        {!selectedFile ? (
          <div className="drop-zone-content">
            <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="drop-zone-text">Drag and drop your XBRL/iXBRL file here</p>
            <p className="drop-zone-subtext">or</p>
            <button 
              className="select-file-btn"
              onClick={handleButtonClick}
              disabled={isValidating}
            >
              Select File
            </button>
            <p className="file-types">Supported: .htm, .html, .xbrl, .xml (Max 50MB)</p>
          </div>
        ) : (
          <div className="selected-file-info">
            <svg className="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div className="file-details">
              <p className="file-name">{selectedFile.name}</p>
              <p className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            {!isValidating && (
              <button 
                className="remove-file-btn"
                onClick={() => {
                  setSelectedFile(null)
                  if (fileInputRef.current) {
                    fileInputRef.current.value = ''
                  }
                }}
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      {selectedFile && !isValidating && (
        <div className="validation-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useDqcRules}
              onChange={(e) => setUseDqcRules(e.target.checked)}
            />
            <span>Enable DQC/DQCRT validation rules</span>
          </label>
          <p className="option-description">
            Data Quality Committee rules provide comprehensive quality checks for XBRL filings
          </p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {isValidating && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="progress-text">
            {uploadProgress < 100 
              ? `Uploading... ${uploadProgress}%` 
              : 'Validating filing...'}
          </p>
        </div>
      )}

      {selectedFile && !isValidating && (
        <button 
          className="upload-btn"
          onClick={handleUpload}
        >
          Upload and Validate
        </button>
      )}
    </div>
  )
}

export default FileUpload
