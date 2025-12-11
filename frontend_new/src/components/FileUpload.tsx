import React, { useCallback } from "react"
import { useDropzone } from "react-dropzone"

interface FileUploadProps {
  onUpload: (file: File) => void
  loading: boolean
}

const FileUpload: React.FC<FileUploadProps> = ({ onUpload, loading }) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onUpload(acceptedFiles[0])
      }
    },
    [onUpload]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
  })

  return (
    <div className="file-upload-container">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? "active" : ""} ${
          loading ? "loading" : ""
        }`}
      >
        <input {...getInputProps()} disabled={loading} />
        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Processing PDF...</p>
          </div>
        ) : (
          <>
            <div className="upload-icon">📄</div>
            <p>
              {isDragActive
                ? "Drop the PDF here..."
                : "Drag & drop a FIR PDF here, or click to select"}
            </p>
            <button className="upload-btn" type="button">
              Select PDF
            </button>
          </>
        )}
      </div>
    </div>
  )
}

export default FileUpload
