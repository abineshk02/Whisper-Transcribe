import React, { useState } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/transcribe";

const TranscribePage = () => {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("");
  const [transcript, setTranscript] = useState("");
  const [downloadLink, setDownloadLink] = useState("");

  const handleUpload = async () => {
    if (!file && !url) {
      alert("Please upload a file or paste a URL!");
      return;
    }

    try {
      setStatus("⏳ Uploading and transcribing...");
      setTranscript("");
      setDownloadLink("");

      let res;

      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("user_id", 1); // replace with actual logged-in user ID

        res = await axios.post(`${API_BASE}/transcribe-file`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
      } else if (url) {
        console.log("Transcribing URL:", url);
        if (!url) {
          alert("Please enter a URL!");
          return;
        }

        res = await axios.post(
          `${API_BASE}/transcribe-url`,
          {
            file_url: url.trim(),
            user_id: 1, // replace with actual logged-in user ID
          },
          { headers: { "Content-Type": "application/json" } }
        );
      }

      console.log("Backend response:", res.data); // Debug: check what keys are returned

      if (!res.data.transcript_filename) {
        throw new Error("Transcript filename missing in backend response");
      }

      setStatus("✅ Transcription completed successfully!");
      setTranscript(res.data.transcript);
      setDownloadLink(`${API_BASE}/download/${res.data.transcript_filename}`);
    } catch (err) {
      console.error(err);
      setStatus("❌ Error: Something went wrong while transcribing.");
    }
  };

  const handleReset = () => {
    setFile(null);
    setUrl("");
    setStatus("");
    setTranscript("");
    setDownloadLink("");
    document.getElementById("fileInput").value = "";
  };

  return (
    <div className="container mt-5">
      <div
        className="card shadow-lg border-0 mx-auto"
        style={{ maxWidth: "500px" }}
      >
        <div className="card-body text-center">
          <h3 className="card-title mb-3 text-primary">
            🎧 Audio/Video Transcriber
          </h3>
          <p className="text-muted mb-4">
            Upload a file or paste a media URL to get an instant transcription.
          </p>

          {/* Option 1: File Upload */}
          <div className="mb-3 text-start">
            <label className="form-label fw-semibold">Upload File:</label>
            <input
              id="fileInput"
              type="file"
              accept="audio/*,video/*"
              onChange={(e) => setFile(e.target.files[0])}
              className="form-control"
            />
          </div>

          <div className="text-center text-muted my-2">OR</div>

          {/* Option 2: URL Input */}
          <div className="mb-3 text-start">
            <label className="form-label fw-semibold">Paste URL:</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/audio.mp3"
              className="form-control"
            />
          </div>

          <button
            onClick={handleUpload}
            className="btn btn-primary w-100"
            disabled={status.includes("Uploading")}
          >
            {status.includes("Uploading")
              ? "Processing..."
              : "Upload / Transcribe"}
          </button>

          <button
            onClick={handleReset}
            className="btn btn-outline-secondary w-100 mt-2"
          >
            🔄 Reset
          </button>

          <div className="mt-4">
            <p className="fw-semibold">{status}</p>

            {transcript && (
              <div
                className="alert alert-light text-start border mt-3"
                style={{ maxHeight: "250px", overflowY: "auto" }}
              >
                <h6 className="fw-bold">Transcript:</h6>
                <p className="small text-muted">{transcript}</p>
              </div>
            )}

            {downloadLink && (
              <a
                href={downloadLink}
                className="btn btn-success mt-2 w-100"
                download
              >
                ⬇️ Download Transcript
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranscribePage;
