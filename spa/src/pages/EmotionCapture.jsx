import { useRef, useCallback, useState, useEffect } from 'react';
import Webcam from 'react-webcam';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

const CAPTURE_INTERVAL_MS = 3000;

export default function EmotionCapture() {
  const { user, updateConsent } = useAuth();
  const webcamRef = useRef(null);
  const intervalRef = useRef(null);
  const [capturing, setCapturing] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [sessionId] = useState(() => crypto.randomUUID());

  const captureAndPredict = useCallback(async () => {
    if (!webcamRef.current) return;
    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return;

    // Convert base64 to blob
    const res = await fetch(screenshot);
    const blob = await res.blob();

    const formData = new FormData();
    formData.append('file', blob, 'frame.jpg');

    try {
      const { data } = await api.post(
        `/emotion/predict?session_id=${sessionId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(data);
      setHistory((prev) => [data, ...prev].slice(0, 20));
    } catch (err) {
      console.error('Prediction error:', err);
    }
  }, [sessionId]);

  const startCapture = useCallback(() => {
    setCapturing(true);
    captureAndPredict();
    intervalRef.current = setInterval(captureAndPredict, CAPTURE_INTERVAL_MS);
  }, [captureAndPredict]);

  const stopCapture = useCallback(() => {
    setCapturing(false);
    clearInterval(intervalRef.current);
  }, []);

  useEffect(() => {
    return () => clearInterval(intervalRef.current);
  }, []);

  const emotionEmoji = {
    Happy: '😊',
    Sad: '😢',
    Angry: '😠',
    Fear: '😨',
    Surprise: '😲',
    Disgust: '🤢',
    Neutral: '😐',
  };

  // Request camera consent if not given
  if (!user?.consent_camera) {
    return (
      <div className="consent-page">
        <div className="consent-card">
          <h2>Camera Access Required</h2>
          <p>
            EmoteFlow uses your webcam to detect emotions and provide
            personalized learning suggestions. Your privacy is important — video
            is processed in real time and not stored.
          </p>
          <button onClick={() => updateConsent(true)}>
            I Consent — Enable Camera
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="capture-page">
      <div className="capture-main">
        <div className="webcam-container">
          <Webcam
            ref={webcamRef}
            audio={false}
            screenshotFormat="image/jpeg"
            videoConstraints={{ width: 480, height: 360, facingMode: 'user' }}
            mirrored
          />
          <div className="webcam-controls">
            {!capturing ? (
              <button className="btn-start" onClick={startCapture}>
                Start Detection
              </button>
            ) : (
              <button className="btn-stop" onClick={stopCapture}>
                Stop Detection
              </button>
            )}
          </div>
        </div>

        {result && (
          <div className="result-panel">
            <div className="emotion-display">
              <span className="emotion-emoji">
                {emotionEmoji[result.emotion] || '🤔'}
              </span>
              <h2>{result.emotion}</h2>
              <p className="confidence">
                {(result.confidence * 100).toFixed(1)}% confidence
              </p>
            </div>

            {result.suggestion && (
              <div className="suggestion-card">
                <h3>Suggestion</h3>
                <p>{result.suggestion}</p>
              </div>
            )}

            <div className="scores-grid">
              {Object.entries(result.scores).map(([emotion, score]) => (
                <div key={emotion} className="score-bar">
                  <span className="score-label">{emotion}</span>
                  <div className="score-track">
                    <div
                      className="score-fill"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="score-value">
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {history.length > 0 && (
        <div className="history-panel">
          <h3>Recent Detections</h3>
          <div className="history-list">
            {history.map((h, i) => (
              <div key={i} className="history-item">
                <span>{emotionEmoji[h.emotion] || '🤔'}</span>
                <span>{h.emotion}</span>
                <span>{(h.confidence * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
