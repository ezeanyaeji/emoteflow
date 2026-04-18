# EmoteFlow

Real-time student emotion recognition and learning engagement platform powered by a CNN model and a rule-based suggestion engine.

EmoteFlow captures facial expressions via webcam, classifies emotions using an ONNX-exported CNN trained on FER2013 + CK+ datasets, and provides actionable learning suggestions in real time. Teachers and admins get dashboards to monitor class-wide emotional trends and individual student analytics.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Seed the Admin Account](#4-seed-the-admin-account)
  - [5. Run the App](#5-run-the-app)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
  - [Authentication](#authentication-auth)
  - [Emotion Recognition](#emotion-recognition-emotion)
  - [Suggestions](#suggestions-suggestion)
  - [Teacher Dashboard](#teacher-dashboard-dashboard)
  - [Admin Management](#admin-management-admin)
  - [Teacher-Student Assignments](#teacher-student-assignments-assignments)
  - [Health Check](#health-check)
- [Authentication Flow](#authentication-flow)
- [Emotion Prediction Pipeline](#emotion-prediction-pipeline)
- [Suggestion Rules](#suggestion-rules)
- [Role-Based Access](#role-based-access)
- [Frontend Pages](#frontend-pages)
- [Testing](#testing)
- [Model Training](#model-training)
- [Deployment](#deployment)
  - [Docker](#docker)
  - [Frontend Hosting](#frontend-hosting)
- [Rate Limiting](#rate-limiting)
- [Database Schema](#database-schema)
- [License](#license)

---

## Features

- **Real-time emotion detection** — 7-class CNN (Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral) via webcam
- **Rule-based learning suggestions** — Actionable feedback mapped to each detected emotion
- **Teacher dashboard** — Class-wide emotion distribution, timeline charts, student activity table, CSV/JSON export
- **Admin dashboard** — User management, platform statistics, teacher account creation, role-based charts
- **Student history** — Personal emotion analytics with pie, bar, and timeline charts
- **Teacher-student assignments** — Teachers and admins can assign specific students to teachers; dashboards filter data accordingly
- **Camera consent flow** — Students must explicitly grant camera permission before predictions
- **JWT authentication** — Access tokens in memory + refresh tokens in httpOnly cookies
- **Rate limiting** — SlowAPI protection on registration, login, and prediction endpoints
- **ONNX Runtime inference** — Model preloaded on startup for zero cold-start latency

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Uvicorn, Motor (async MongoDB), Pydantic v2 |
| **Frontend** | React 18, React Router v6, Recharts, React Webcam, Vite |
| **ML Inference** | ONNX Runtime, OpenCV (Haar cascade face detection) |
| **ML Training** | TensorFlow/Keras, FER2013 + CK+ datasets |
| **Database** | MongoDB Atlas |
| **Auth** | python-jose (JWT), passlib + bcrypt |
| **Rate Limiting** | SlowAPI |
| **Model Hosting** | Hugging Face Hub |
| **Containerisation** | Docker (Python 3.12-slim) |

---

## Project Structure

```
EmoteFlow/
├── api/                           # Backend (FastAPI)
│   ├── core/
│   │   ├── config.py              # Pydantic Settings (env vars)
│   │   ├── database.py            # MongoDB connection + collections
│   │   ├── dependencies.py        # Auth dependency injection
│   │   ├── rate_limit.py          # SlowAPI limiter instance
│   │   └── security.py            # JWT creation/verification, password hashing
│   ├── models/
│   │   ├── user.py                # User, token, role schemas
│   │   ├── emotion.py             # Emotion result & history schemas
│   │   ├── suggestion.py          # Suggestion & feedback schemas
│   │   └── assignment.py          # Teacher-student assignment schemas
│   ├── routers/
│   │   ├── auth.py                # /auth endpoints
│   │   ├── emotion.py             # /emotion endpoints
│   │   ├── suggestion.py          # /suggestion endpoints
│   │   ├── dashboard.py           # /dashboard endpoints
│   │   ├── admin.py               # /admin endpoints
│   │   └── assignment.py          # /assignments endpoints
│   ├── services/
│   │   ├── auth.py                # Register, login, refresh logic
│   │   ├── emotion.py             # ONNX model loading & prediction
│   │   ├── suggestion.py          # Rule-based suggestion engine
│   │   ├── dashboard.py           # Aggregation queries for dashboards
│   │   └── assignment.py          # Student assignment CRUD
│   ├── tests/
│   │   ├── conftest.py            # Fake in-memory MongoDB, test fixtures
│   │   ├── test_auth.py           # 8 auth tests
│   │   ├── test_admin.py          # 6 admin tests
│   │   └── test_emotion.py        # 5 emotion tests
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Container configuration
├── spa/                           # Frontend (React SPA)
│   ├── src/
│   │   ├── App.jsx                # Routes & role-based redirects
│   │   ├── main.jsx               # React entry point
│   │   ├── styles.css             # Global stylesheet
│   │   ├── api/
│   │   │   └── axios.js           # Axios instance with JWT interceptors
│   │   ├── context/
│   │   │   └── AuthContext.jsx    # Auth state provider
│   │   ├── pages/
│   │   │   ├── Login.jsx          # Login form
│   │   │   ├── Register.jsx       # Registration form
│   │   │   ├── EmotionCapture.jsx # Webcam + real-time prediction
│   │   │   ├── Dashboard.jsx      # Teacher class overview
│   │   │   ├── AdminDashboard.jsx # Admin management panel
│   │   │   ├── StudentDetail.jsx  # Individual student analytics
│   │   │   └── MyHistory.jsx      # Student's own emotion history
│   │   └── components/
│   │       ├── Layout.jsx         # Navbar + role-based nav links
│   │       └── Spinner.jsx        # Loading spinner
│   ├── public/
│   │   └── _redirects             # SPA routing (Netlify/Render)
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── emotion_predictor.py           # Standalone ONNX predictor class
├── train_emotion_cnn.py           # Model training script (TF/Keras → ONNX)
├── emoteflow_training.ipynb       # Kaggle training notebook
├── seed_admin.py                  # Seed default admin account
├── app_documentation.md           # Project documentation
└── app_requirements.md            # Requirements specification
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **MongoDB Atlas** account (or local MongoDB instance)
- **Git**

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ezeanyaeji/EmoteFlow.git
cd EmoteFlow
```

### 2. Backend Setup

Create a virtual environment and install dependencies:

```bash
python -m venv emoteflow_env

# Windows
emoteflow_env\Scripts\activate

# macOS/Linux
source emoteflow_env/bin/activate

cd api
pip install -r requirements.txt
```

Create an `.env` file inside the `api/` directory:

```env
MONGODB_HOST=cluster0.example.mongodb.net
MONGODB_USER=your_db_username
MONGODB_PASSWORD=your_db_password
MONGODB_DB_NAME=emoteflowDB
JWT_SECRET_KEY=your-secure-random-secret-key
CORS_ORIGINS=http://localhost:3000
ADMIN_EMAIL=admin@yourschool.edu
ADMIN_PASSWORD=a-strong-admin-password
```

> **Important:** `MONGODB_HOST`, `MONGODB_USER`, `MONGODB_PASSWORD`, and `JWT_SECRET_KEY` have no defaults and must be set.

### 3. Frontend Setup

```bash
cd spa
npm install
```

### 4. Seed the Admin Account

From the project root (with the venv activated):

```bash
python seed_admin.py
```

This creates the initial admin user using the `ADMIN_EMAIL` and `ADMIN_PASSWORD` from your `.env` file.

### 5. Run the App

**Start the backend** (from the `api/` directory):

```bash
uvicorn main:app --reload --port 8000
```

**Start the frontend** (from the `spa/` directory, in a separate terminal):

```bash
npm run dev
```

Open **http://localhost:3000** in your browser. The Vite dev server proxies `/api` requests to the backend on port 8000.

---

## Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MONGODB_HOST` | str | *required* | MongoDB Atlas hostname |
| `MONGODB_USER` | str | *required* | MongoDB username (URL-encoded) |
| `MONGODB_PASSWORD` | str | *required* | MongoDB password (URL-encoded) |
| `MONGODB_DB_NAME` | str | `emoteflowDB` | Database name |
| `JWT_SECRET_KEY` | str | *required* | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | str | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | Access token lifetime in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | Refresh token lifetime in days |
| `CORS_ORIGINS` | str | `http://localhost:3000` | Comma-separated allowed origins |
| `HF_REPO_ID` | str | `charlykso/emoteflow-emotion-cnn` | Hugging Face model repository |
| `ONNX_FILENAME` | str | `emoteflow_model.onnx` | ONNX model file name |
| `ADMIN_EMAIL` | str | `admin@gmail.com` | Default admin email |
| `ADMIN_PASSWORD` | str | `password` | Default admin password |
| `APP_NAME` | str | `EmoteFlow API` | Application display name |
| `DEBUG` | bool | `false` | Enable debug mode |

---

## API Reference

All endpoints are prefixed with `/api`.

### Authentication (`/auth`)

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| `POST` | `/auth/register` | — | 5/min | Register a new student account |
| `POST` | `/auth/login` | — | 10/min | Login; returns `access_token` and sets `refresh_token` cookie |
| `POST` | `/auth/refresh` | Cookie | — | Refresh the access token using the httpOnly cookie |
| `POST` | `/auth/logout` | JWT | — | Logout and clear the refresh cookie |
| `GET` | `/auth/me` | JWT | — | Get current user profile |
| `PATCH` | `/auth/me` | JWT | — | Update name or camera consent |

**Register request body:**

```json
{
  "email": "student@school.edu",
  "password": "minimum8chars",
  "first_name": "Jane",
  "last_name": "Doe"
}
```

**Login response:**

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

### Emotion Recognition (`/emotion`)

| Method | Endpoint | Auth | Rate Limit | Description |
|--------|----------|------|------------|-------------|
| `POST` | `/emotion/predict` | JWT | 30/min | Upload a face image; returns emotion + suggestion |
| `GET` | `/emotion/history` | JWT | — | List the user's emotion logs (paginated) |
| `GET` | `/emotion/my-summary` | JWT | — | Student's own emotion analytics |

**Predict** — Send a face image as `multipart/form-data` with the field name `file`. The student must have `consent_camera: true` or the request is rejected with `403`.

**Response:**

```json
{
  "emotion": "Happy",
  "confidence": 0.92,
  "scores": {
    "Angry": 0.01, "Disgust": 0.0, "Fear": 0.02,
    "Happy": 0.92, "Sad": 0.01, "Surprise": 0.03, "Neutral": 0.01
  },
  "suggestion": {
    "emotion": "Happy",
    "action": "Continue current activity or try a harder challenge",
    "description": "The student appears engaged. Maintain momentum or increase difficulty.",
    "category": "challenge"
  }
}
```

**History query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | str | — | Filter by session |
| `limit` | int | `50` | Results per page (1–200) |
| `skip` | int | `0` | Offset for pagination |
| `hours` | int | `24` | Time window (1–720) |

### Suggestions (`/suggestion`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/suggestion/rules/{emotion}` | JWT | Get all suggestion rules for a given emotion |
| `GET` | `/suggestion/history` | JWT | User's suggestion log (paginated) |
| `POST` | `/suggestion/feedback` | JWT | Submit feedback on a received suggestion |

### Teacher Dashboard (`/dashboard`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/dashboard/summary` | Teacher/Admin | Class emotion aggregates (distribution, timeline, student list) |
| `GET` | `/dashboard/export` | Teacher/Admin | Export data as CSV or JSON |
| `GET` | `/dashboard/student/{student_id}` | Teacher/Admin | Individual student analytics |

**Query parameters:** `hours` (1–720, default 24), `session_id` (optional), `format` (json/csv for export).

> Dashboard data is automatically filtered to only show students assigned to the teacher. If no assignments exist, all students are shown (backwards compatible).

### Admin Management (`/admin`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/admin/teachers` | Admin | Create a teacher account |
| `GET` | `/admin/users` | Admin | List users (filter by role, paginated) |
| `DELETE` | `/admin/users/{user_id}` | Admin | Delete a user (cannot delete self) |
| `GET` | `/admin/stats` | Admin | Platform-wide statistics |
| `GET` | `/admin/assignments/{teacher_id}` | Admin | View a teacher's assigned students |
| `PUT` | `/admin/assignments/{teacher_id}` | Admin | Set a teacher's full student list |

### Teacher-Student Assignments (`/assignments`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/assignments/my-students` | Teacher/Admin | List assigned student IDs |
| `PUT` | `/assignments/my-students` | Teacher/Admin | Replace the full student list |
| `POST` | `/assignments/my-students` | Teacher/Admin | Add students to the list |
| `DELETE` | `/assignments/my-students` | Teacher/Admin | Remove students from the list |
| `GET` | `/assignments/available-students` | Teacher/Admin | Search all students by name/email |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Returns `{ "status": "ok" }` |
| `GET` / `HEAD` | `/` | Root status endpoint |

---

## Authentication Flow

```
┌──────────┐     POST /auth/login      ┌──────────┐
│  Client   │ ─────────────────────────▶│  Server  │
│           │◀───── access_token (JSON) │          │
│           │◀───── refresh_token (cookie, httpOnly)│
└──────────┘                            └──────────┘

On each API request:
  Authorization: Bearer <access_token>

When access token expires (401):
  POST /auth/refresh  →  new access_token
  Retry original request automatically (Axios interceptor)
```

- **Access tokens** are stored in memory (not localStorage) to prevent XSS theft
- **Refresh tokens** are stored as `httpOnly`, `secure`, `SameSite=None` cookies
- Passwords are hashed with **bcrypt** before storage

---

## Emotion Prediction Pipeline

```
Webcam Frame
    │
    ▼
Haar Cascade Face Detection (OpenCV)
    │
    ▼
Crop face → Grayscale → Resize to 48×48
    │
    ▼
CLAHE Contrast Normalization
    │
    ▼
Normalize pixel values to [0, 1]
    │
    ▼
ONNX Runtime Inference (shape: 1×48×48×1)
    │
    ▼
Softmax → 7 emotion scores
    │
    ▼
Top emotion + confidence + all scores
    │
    ▼
Rule-based suggestion lookup
    │
    ▼
Log emotion + suggestion to MongoDB
```

The ONNX model is downloaded from Hugging Face Hub on first startup and cached locally.

---

## Suggestion Rules

The rule-based engine maps detected emotions to learning suggestions:

| Emotion | Action | Category |
|---------|--------|----------|
| **Happy** | Continue current activity or try a harder challenge | Challenge |
| | Introduce group collaboration | Interactive |
| **Sad** | Take a short break | Break |
| | Revisit simpler material | Review |
| **Fear** | Review concept with guided examples | Review |
| | Offer encouragement and reassurance | Calming |
| **Angry** | Pause learning, try a calming activity | Calming |
| | Switch to a different topic | Interactive |
| **Surprise** | Explore the surprising concept further | Challenge |
| **Disgust** | Change activity or presentation style | Interactive |
| **Neutral** | Switch to interactive exercises | Interactive |
| | Ask a thought-provoking question | Challenge |

---

## Role-Based Access

| Feature | Student | Teacher | Admin |
|---------|:-------:|:-------:|:-----:|
| Register / Login | ✓ | ✓ | ✓ |
| Webcam emotion capture | ✓ | — | — |
| View own emotion history | ✓ | — | — |
| Class dashboard & export | — | ✓ | ✓ |
| View individual student detail | — | ✓ | ✓ |
| Manage own student assignments | — | ✓ | ✓ |
| Create teacher accounts | — | — | ✓ |
| Manage all users | — | — | ✓ |
| Assign students to any teacher | — | — | ✓ |
| Platform-wide statistics | — | — | ✓ |

---

## Frontend Pages

### Login & Register

Standard email/password forms. New registrations default to the **student** role. After login the app redirects based on role:

- **Student** → Emotion Capture page
- **Teacher** → Class Dashboard
- **Admin** → Admin Dashboard

### Emotion Capture (Student)

1. Grant camera consent (one-time, saved to profile)
2. Webcam feed activates with a **Start Capture** button
3. Each capture sends a frame to `POST /emotion/predict`
4. Results show: detected emotion with emoji, confidence score, per-class score bars, suggestion card, and recent detection history

### My History (Student)

Personal analytics page with selectable time ranges (1h, 6h, 24h, 7d):

- Summary stat cards (total detections, dominant emotion, average confidence)
- Emotion distribution pie chart
- Emotion frequency bar chart
- Emotion timeline line chart
- Recent detections table

### Dashboard (Teacher)

Class-level overview filtered to assigned students:

- Time range selector with CSV/JSON export buttons
- Stats cards (total students, detections, active count, dominant emotion)
- Emotion distribution pie chart + frequency bar chart
- Student activity table (clickable rows open individual student detail)
- **Manage Students** panel — search and assign students via checkboxes

### Admin Dashboard

Full platform management:

- Platform stats (total users by role, emotion logs, active students)
- Users by Role bar chart + Emotion Distribution pie chart
- **Create Teacher** form
- **All Users** table with role filter and delete capability
- **Assign Students to Teacher** — select a teacher, search students, toggle checkboxes, save
- Recent registrations table

### Student Detail (Teacher/Admin)

Deep dive into one student's emotions (navigated from dashboard student table):

- Emotion distribution, timeline, recent detections
- Back button to return to the dashboard

---

## Testing

Tests use an in-memory fake MongoDB (no real database needed) and `httpx.AsyncClient`.

```bash
cd api
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v
```

**Test coverage (21 tests):**

| File | Tests | Coverage |
|------|-------|----------|
| `test_auth.py` | 8 | Register (success, duplicate, short password), Login (success, wrong password, unknown email), Me (auth, no-token), Logout |
| `test_admin.py` | 6 | Stats (admin, student-forbidden), Create teacher (success, student-forbidden), Delete user (success, self-blocked) |
| `test_emotion.py` | 5 | Predict (success, no-consent, non-image, unauth), History (empty, with-data) |

---

## Model Training

The CNN model is trained outside the main app using:

- **`train_emotion_cnn.py`** — CLI training script
- **`emoteflow_training.ipynb`** — Kaggle notebook (GPU environment)

### Training Details

| Parameter | Value |
|-----------|-------|
| Architecture | Custom CNN |
| Primary dataset | FER2013 (Kaggle) |
| Fine-tuning dataset | CK+ (Cohn-Kanade Extended) |
| Image size | 48×48 grayscale |
| Batch size | 64 |
| Epochs | 50 (initial) + 20 (fine-tune) |
| Learning rate | 1e-3 → 1e-4 (fine-tune) |
| Augmentation | Rotation ±15°, shift ±10%, horizontal flip, zoom ±10% |
| Output | `.keras` → ONNX export → Hugging Face Hub |

### Standalone Predictor

`emotion_predictor.py` provides a self-contained `EmotionPredictor` class for use outside the web app:

```python
from emotion_predictor import EmotionPredictor

predictor = EmotionPredictor()
result = predictor.predict(image_bgr)
# {'emotion': 'Happy', 'confidence': 0.92, 'scores': {...}}
```

---

## Deployment

### Docker

Build and run the backend:

```bash
cd api
docker build -t emoteflow-api .
docker run -p 10000:10000 --env-file .env emoteflow-api
```

The Dockerfile uses Python 3.12-slim with OpenCV system dependencies (`libgl1-mesa-glx`, `libglib2.0-0`). The server listens on port `10000` (or the `PORT` env var).

### Frontend Hosting

Build the SPA for production:

```bash
cd spa
npm run build
```

The `dist/` output is a static site deployable to Netlify, Render, Vercel, or any static host. The `_redirects` file in `public/` handles SPA client-side routing.

Set the `VITE_API_URL` environment variable to point to your deployed backend (e.g., `https://emoteflow-api.onrender.com/api`).

---

## Rate Limiting

IP-based rate limits protect critical endpoints:

| Endpoint | Limit |
|----------|-------|
| `POST /auth/register` | 5 requests/minute |
| `POST /auth/login` | 10 requests/minute |
| `POST /emotion/predict` | 30 requests/minute |

Exceeding the limit returns `429 Too Many Requests`.

---

## Database Schema

**MongoDB collections:**

### `users`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | Auto-generated |
| `email` | string | Unique index |
| `hashed_password` | string | bcrypt hash |
| `first_name` | string | |
| `last_name` | string | |
| `role` | string | `student`, `teacher`, or `admin` |
| `consent_camera` | bool | Default `false` |
| `is_active` | bool | Default `true` |
| `created_at` | datetime | |

### `emotions`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `user_id` | string | |
| `session_id` | string | |
| `emotion` | string | One of 7 classes |
| `confidence` | float | 0–1 |
| `scores` | object | All 7 emotion scores |
| `timestamp` | datetime | Indexed with `user_id` (DESC) |

### `suggestions`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `user_id` | string | |
| `session_id` | string | |
| `emotion` | string | |
| `suggestion` | object | `{emotion, action, description, category}` |
| `feedback` | string | Optional, max 500 chars |
| `timestamp` | datetime | Indexed with `user_id` (DESC) |

### `assignments`

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | |
| `teacher_id` | string | Unique compound index |
| `student_id` | string | with `teacher_id` |

---

## License

This project is developed for academic purposes.
