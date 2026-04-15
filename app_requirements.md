# EmoteFlow Web Application Requirements

## 📋 Functional Requirements
1. **User Authentication**
   - Secure login with JWT-based authentication.
   - Role-based access: student, teacher, admin.

2. **Camera Integration**
   - Real-time webcam capture via browser (WebRTC).
   - Face detection preprocessing (OpenCV, MTCNN).

3. **Emotion Recognition**
   - CNN model trained on emotion datasets (FER2013, AffectNet, CK+).
   - Inference pipeline integrated with FastAPI endpoints.
   - Confidence scoring for predictions.

4. **Suggestion Engine**
   - Rule-based mapping of emotions → suggested actions.
   - Future extension: reinforcement learning for personalization.

5. **Data Storage (MongoDB)**
   - Student profiles (name, ID, learning history).
   - Emotion logs (timestamp, emotion, confidence).
   - Suggested actions and feedback loops.

6. **Teacher Dashboard**
   - Aggregate emotion trends across class.
   - Export reports (CSV/JSON).
   - Visualizations (charts of engagement, frustration, etc.).

7. **Privacy & Consent**
   - Explicit opt-in for camera use.
   - Anonymization of stored emotion data.
   - Compliance with ethical standards.

---

## ⚙️ Non-Functional Requirements
- **Performance**: Real-time inference (<200ms per frame).
- **Scalability**: Handle multiple concurrent student sessions.
- **Security**: Encrypted communication (HTTPS), secure JWT tokens.
- **Maintainability**: Modular FastAPI services, clean MongoDB schema.
- **Portability**: Deployable via Docker/Kubernetes.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python) for REST APIs.
- **Database**: MongoDB for flexible document storage.
- **Model Serving**: TensorFlow/PyTorch → ONNX → FastAPI endpoint.
- **Frontend**: React/Next.js with WebRTC for camera streaming.
- **Deployment**: Docker + Kubernetes, CI/CD pipeline.

---

## 🚀 Next Steps
1. Define **MongoDB schema** (students, emotions, suggestions).
2. Set up **FastAPI endpoints**:
   - `/auth` (login/register)
   - `/emotion` (upload frame → CNN inference)
   - `/suggestion` (map emotion → action)
   - `/dashboard` (teacher analytics)
3. Integrate **CNN model** into FastAPI service.
4. Build **frontend prototype** for student interaction.
