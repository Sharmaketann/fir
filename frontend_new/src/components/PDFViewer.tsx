import React, { useEffect, useState } from "react"

interface PDFViewerProps {
  fileId: string
}

const PDFViewer: React.FC<PDFViewerProps> = ({ fileId }) => {
  const [pdfUrl, setPdfUrl] = useState<string>("")

  useEffect(() => {
    if (fileId) {
      setPdfUrl(`http://localhost:8000/api/file/${fileId}`)
    }
  }, [fileId])

  if (!pdfUrl) {
    return (
      <div className="pdf-viewer">
        <p>No PDF loaded</p>
      </div>
    )
  }

  return (
    <div className="pdf-viewer">
      <iframe
        src={pdfUrl}
        width="100%"
        height="600px"
        style={{ border: "1px solid #ccc", borderRadius: "4px" }}
        title="FIR Document"
      >
        <p>
          Your browser does not support iframes.
          <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
            Click here to view the PDF
          </a>
        </p>
      </iframe>
    </div>
  )
}

export default PDFViewer
