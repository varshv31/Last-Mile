# Last-Mile Delivery Tracker

A comprehensive full-stack solution for tracking, managing, and dispatching last-mile deliveries.

## 🚀 Tech Stack

### Frontend
- **Framework**: React via [TanStack Start](https://tanstack.com/start/latest) and Vite
- **Styling**: Tailwind CSS & Shadcn UI
- **Routing & State**: TanStack Router & TanStack Query

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: PostgreSQL (via asyncpg)
- **ORM & Migrations**: SQLAlchemy & Alembic
- **Authentication**: JWT Tokens (python-jose)

## 📁 Project Structure

```text
.
├── backend/          # FastAPI Python application
├── frontend/         # React/Vite frontend application
├── render.yaml       # Render Blueprint for automated backend deployment
└── .gitignore        # Root gitignore
```

## 🛠️ Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (3.12+)
- **PostgreSQL** (Local installation or a cloud provider like Supabase)

---

## 💻 Local Development Setup

### 1. Backend Setup

Open a terminal and navigate to the `backend` directory:
```bash
cd backend
```

**Create and activate a virtual environment:**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in the `backend` directory (you can copy `.env.example`). Update the `DATABASE_URL` and `JWT_SECRET_KEY`.

**Run Database Migrations:**
```bash
alembic upgrade head
```

**Start the Development Server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Frontend Setup

Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Environment Variables:**
Create a `.env` (or `.env.local`) file in the `frontend` directory if it doesn't exist. Make sure the API URL points to your local backend:
```env
VITE_API_BASE_URL=http://localhost:8000
```

**Start the Development Server:**
```bash
npm run dev
```
The app will be available at [https://last-mile-teal.vercel.app](https://last-mile-teal.vercel.app)

---

