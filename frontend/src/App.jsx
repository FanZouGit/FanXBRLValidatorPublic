import { useState } from 'react'
import './aws-config'
import FileUpload from './components/FileUpload'
import ValidationResults from './components/ValidationResults'
import './App.css'

function App() {
  const [validationResults, setValidationResults] = useState(null)
  const [isValidating, setIsValidating] = useState(false)

  const handleValidationComplete = (results) => {
    setValidationResults(results)
    setIsValidating(false)
  }

  const handleValidationStart = () => {
    setIsValidating(true)
    setValidationResults(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>XBRL Validator</h1>
        <p className="subtitle">Upload and Validate EDGAR XBRL and iXBRL Filings</p>
      </header>

      <main className="app-main">
        <FileUpload 
          onValidationStart={handleValidationStart}
          onValidationComplete={handleValidationComplete}
          isValidating={isValidating}
        />

        {validationResults && (
          <ValidationResults results={validationResults} />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Powered by Arelle XBRL Validation Engine | 
          AWS Lambda & S3 Backend
        </p>
      </footer>
    </div>
  )
}

export default App
