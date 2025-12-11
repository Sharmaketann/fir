import React, { useState } from "react"

interface ExtractionResultsProps {
  data: any
  fullData?: any
}

const ExtractionResults: React.FC<ExtractionResultsProps> = ({
  data,
  fullData,
}) => {
  const [editMode, setEditMode] = useState(false)
  const [editedData, setEditedData] = useState(JSON.stringify(data, null, 2))

  const handleSave = async () => {
    try {
      const parsedData = JSON.parse(editedData)
      const trainingSample = {
        file_id: fullData?.file_id || "unknown",
        ocr_data: fullData?.text_data || {},
        corrected_data: parsedData,
      }

      const response = await fetch("http://localhost:8000/api/train/sample", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trainingSample),
      })

      if (response.ok) {
        alert(
          "Corrections saved as training data! The model will improve with more samples."
        )
        setEditMode(false)
      } else {
        throw new Error("Failed to save")
      }
    } catch (error) {
      console.error("Save error:", error)
      alert("Failed to save training data")
    }
  }

  const handleRetrain = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/train/retrain", {
        method: "POST",
      })

      const result = await response.json()
      alert(result.message || "Model retrained successfully!")
    } catch (error) {
      console.error("Retrain error:", error)
      alert("Failed to retrain model")
    }
  }

  const downloadJSON = () => {
    const dataStr = JSON.stringify(data, null, 2)
    const dataBlob = new Blob([dataStr], { type: "application/json" })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement("a")
    link.href = url
    link.download = "fir_extracted_data.json"
    link.click()
  }

  return (
    <div className="extraction-results">
      <div className="results-header">
        <h2>Extracted Information</h2>
        <div className="button-group">
          <button onClick={() => setEditMode(!editMode)}>
            {editMode ? "Cancel" : "Edit"}
          </button>
          {editMode && <button onClick={handleSave}>Save & Train</button>}
          <button onClick={handleRetrain}>Retrain Model</button>
          <button onClick={downloadJSON}>Download JSON</button>
        </div>
      </div>

      <div className="results-content">
        {editMode ? (
          <textarea
            className="json-editor"
            value={editedData}
            onChange={(e) => setEditedData(e.target.value)}
            rows={20}
          />
        ) : (
          <pre className="json-display">{JSON.stringify(data, null, 2)}</pre>
        )}
      </div>
    </div>
  )
}

export default ExtractionResults
