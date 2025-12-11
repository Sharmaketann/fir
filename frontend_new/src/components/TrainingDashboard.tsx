import React, { useState, useEffect } from "react"

interface TrainingSample {
  file_id: string
  ocr_data: any
  ground_truth: any
}

const TrainingDashboard: React.FC = () => {
  const [samples, setSamples] = useState<TrainingSample[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadTrainingSamples()
  }, [])

  const loadTrainingSamples = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/train/samples")
      const data = await response.json()
      setSamples(data.samples || [])
    } catch (error) {
      console.error("Failed to load samples:", error)
    }
  }

  const handleRetrain = async () => {
    setLoading(true)
    try {
      const response = await fetch("http://localhost:8000/api/train/retrain", {
        method: "POST",
      })
      const result = await response.json()
      alert(result.message || "Model retrained successfully!")
      loadTrainingSamples() // Refresh the samples
    } catch (error) {
      console.error("Retrain error:", error)
      alert("Failed to retrain model")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="training-dashboard">
      <h2>Model Training Dashboard</h2>

      <div className="training-stats">
        <div className="stat-card">
          <h3>Total Samples</h3>
          <p>{samples.length}</p>
        </div>
        <div className="stat-card">
          <h3>Status</h3>
          <p>
            {samples.length >= 5 ? "Ready to Retrain" : "Need More Samples"}
          </p>
        </div>
      </div>

      <div className="training-actions">
        <button
          onClick={handleRetrain}
          disabled={loading || samples.length < 5}
          className="retrain-button"
        >
          {loading ? "Retraining..." : "Retrain Model"}
        </button>
        <button onClick={loadTrainingSamples} className="refresh-button">
          Refresh Samples
        </button>
      </div>

      <div className="samples-list">
        <h3>Training Samples</h3>
        {samples.length === 0 ? (
          <p>
            No training samples yet. Edit and save corrections to create
            training data.
          </p>
        ) : (
          <div className="samples-grid">
            {samples.map((sample, index) => (
              <div key={index} className="sample-card">
                <h4>Sample {index + 1}</h4>
                <p>
                  <strong>File ID:</strong> {sample.file_id}
                </p>
                <details>
                  <summary>Ground Truth Data</summary>
                  <pre>{JSON.stringify(sample.ground_truth, null, 2)}</pre>
                </details>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TrainingDashboard
