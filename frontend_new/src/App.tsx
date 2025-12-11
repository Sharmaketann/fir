import React, { useState } from "react"
import FileUpload from "./components/FileUpload"
import PDFViewer from "./components/PDFViewer"
import ExtractionResults from "./components/ExtractionResults"
import TrainingDashboard from "./components/TrainingDashboard"
import "./App.css"

interface ExtractionData {
  file_id: string
  filename: string
  extracted_fields: any
  text_data: any
}

function App() {
  const [extractionData, setExtractionData] = useState<ExtractionData | null>(
    null
  )
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<"extraction" | "training">(
    "extraction"
  )

  const handleUpload = async (file: File) => {
    setLoading(true)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Upload failed")
      }

      const data = await response.json()
      setExtractionData(data)
    } catch (error) {
      console.error("Upload error:", error)
      alert("Failed to process file")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>FIR Document Extraction System</h1>
      </header>

      <div className="tab-navigation">
        <button
          className={activeTab === "extraction" ? "active" : ""}
          onClick={() => setActiveTab("extraction")}
        >
          Document Extraction
        </button>
        <button
          className={activeTab === "training" ? "active" : ""}
          onClick={() => setActiveTab("training")}
        >
          Model Training
        </button>
      </div>

      <div className="main-container">
        {activeTab === "extraction" ? (
          <>
            <div className="upload-section">
              <FileUpload onUpload={handleUpload} loading={loading} />
            </div>

            {extractionData && (
              <div className="content-grid">
                <div className="pdf-section">
                  <PDFViewer fileId={extractionData.file_id} />
                </div>

                <div className="results-section">
                  <ExtractionResults
                    data={extractionData.extracted_fields}
                    fullData={extractionData}
                  />
                </div>
              </div>
            )}
          </>
        ) : (
          <TrainingDashboard />
        )}
      </div>
    </div>
  )
}

export default App
