# EmoteFlow Web Application Documentation

## 📖 Project Overview
EmoteFlow is a web application designed to capture students’ emotions through their webcam using Convolutional Neural Networks (CNNs). Based on detected emotions, the system provides rule-based suggestions to enhance learning engagement. The backend is implemented with **FastAPI** and **MongoDB**, while the frontend uses **React/Next.js** with WebRTC for real-time camera streaming.

---

## 🎯 Objectives
- Detect student emotions in real-time using CNN models.
- Provide actionable, rule-based suggestions to improve learning outcomes.
- Store emotion logs and suggestions for analysis.
- Offer a teacher dashboard to visualize class-wide emotional trends.
- Ensure privacy, consent, and ethical handling of student data.

---

## 📋 Functional Requirements
1. **User Authentication**
   - JWT-based secure login.
   - Role-based access: student, teacher, admin.

2. **Camera Integration**
   - Real-time webcam capture (WebRTC).
   - Face detection preprocessing (OpenCV, MTCNN).

3. **Emotion Recognition**
   - CNN trained on **FER2013** dataset.
   - Fine-tuned with **CK+** dataset for improved accuracy.
   - Confidence scoring for predictions.

4. **Suggestion Engine**
   - Rule-based mapping of emotions → suggested actions.
   - Examples:
     - Happy → Continue activity / harder challenge.
     - Sad → Take a break / revisit simpler material.
     - Confused → Review last concept / ask teacher.
     - Neutral → Switch to interactive exercises.
     - Angry → Pause learning / calming activity.

5. **Data Storage (MongoDB)**
   - **Students Collection**: profile info, learning history.
   - **Emotions Collection**: timestamp, emotion, confidence.
   - **Suggestions Collection**: mapped actions, feedback.

6. **Teacher Dashboard**
   - Aggregate emotion trends across class.
   - Export reports (CSV/JSON).
   - Visualizations (charts of engagement, frustration, etc.).

7. **Privacy & Consent**
   - Explicit opt-in for camera use.
   - Anonymization of emotion data.
   - Compliance with ethical standards.

---

## ⚙️ Non-Functional Requirements
- **Performance**: Real-time inference (<200ms per frame).
- **Scalability**: Support multiple concurrent student sessions.
- **Security**: HTTPS encryption, secure JWT tokens.
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

## 📚 Datasets
- **FER2013 (Kaggle)**: Primary dataset for CNN training.
- **CK+ (Cohn-Kanade Extended)**: Fine-tuning and validation dataset.
- **Future Extensions**: AffectNet or RAF-DB for robustness.

---

## 🚀 Next Steps
1. Define **MongoDB schema** (students, emotions, suggestions).
2. Implement **FastAPI endpoints**:
   - `/auth` → login/register
   - `/emotion` → frame upload → CNN inference
   - `/suggestion` → emotion → action mapping
   - `/dashboard` → teacher analytics
3. Integrate CNN model into FastAPI service.
4. Build frontend prototype for student interaction.
5. Document reinforcement learning as **future work** for personalization.

---

## 📌 Academic Contribution
- **Baseline**: CNN-based emotion recognition using FER2013.
- **Novelty**: Fine-tuning with CK+ for improved accuracy + rule-based educational suggestion engine.
- **Future Work**: Reinforcement learning for adaptive, personalized suggestions.
