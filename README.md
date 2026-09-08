# CareFlow AI

AI-powered Hospital Management Platform with separate Patient and Admin portals.

## Tech Stack

- **Frontend:** React, Vite, TypeScript, Tailwind CSS, React Router, Axios
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, JWT Authentication
- **Database:** PostgreSQL 16
- **AI:** Ollama (configurable model)
- **Containerization:** Docker, Docker Compose

## Project Structure

```
careflow-ai/
├── frontend/          # React + Vite frontend
├── backend/           # FastAPI backend
├── database/          # Database scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
cd careflow-ai

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up --build
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Start PostgreSQL (via Docker or local)
docker compose up db -d

# Run the backend
python run.py
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Ollama | http://localhost:11434 |

## Default Admin Credentials

- **Email:** admin@careflow.ai
- **Password:** admin123

> ⚠️ Change these credentials in production!

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_USER | PostgreSQL username | careflow |
| POSTGRES_PASSWORD | PostgreSQL password | careflow_secret |
| POSTGRES_DB | PostgreSQL database name | careflow_ai |
| DATABASE_URL | Full database connection string | postgresql://careflow:careflow_secret@db:5432/careflow_ai |
| JWT_SECRET_KEY | JWT signing secret | change-me-in-production |
| JWT_ALGORITHM | JWT algorithm | HS256 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry in minutes | 30 |
| OLLAMA_BASE_URL | Ollama service URL | http://ollama:11434 |
| OLLAMA_MODEL | Ollama model to use | llama3 |
| CORS_ORIGINS | Allowed CORS origins | http://localhost:5173 |
| ADMIN_EMAIL | Default admin email | admin@careflow.ai |
| ADMIN_PASSWORD | Default admin password | admin123 |

## Portals

### Patient Portal (`/user/*`)
- Dashboard
- Symptom Analysis
- Doctors Directory
- Appointments
- Payments
- Queue Tokens
- Medical History
- Profile

### Admin Portal (`/admin/*`)
- Dashboard
- User Management
- Doctor Management
- Appointment Management
- Token Management
- Payment Management
- Consultations
- Medical Records
- Reports
- System Settings

## Phase 1 (Foundation) - Implemented

- ✅ React frontend with Vite + Tailwind
- ✅ FastAPI backend with proper structure
- ✅ PostgreSQL with SQLAlchemy
- ✅ JWT authentication (patient & admin)
- ✅ Role-based route protection
- ✅ Separate Patient and Admin portals
- ✅ All portal pages with navigation
- ✅ AI service abstraction (Ollama)
- ✅ Docker configuration
- ✅ Environment variables
- ✅ Health check endpoints
- ✅ Admin seed account

## Phase 2 (Planned)

- ❌ Complete appointment booking system
- ❌ Doctor management (CRUD)
- ❌ Patient profile management
- ❌ AI symptom analysis (Ollama integration)
- ❌ Token/queue system
- ❌ Payment integration
- ❌ Medical records management
- ❌ Consultation notes
- ❌ Admin reports and analytics
- ❌ ML-based predictions
- ❌ Voice registration
- ❌ Real-time notifications
- ❌ File upload (reports, prescriptions)

## License

MIT License
