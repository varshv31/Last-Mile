<div align="center">
  <h1>🚚 SwiftRoute</h1>
  <p><strong>A Modern, Full-Stack Last-Mile Delivery & Logistics Tracking Platform</strong></p>
  
  [![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://last-mile-teal.vercel.app)
  [![Backend API](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://lmd-backend-9s02.onrender.com/docs)
</div>

---

## 📖 Overview

**SwiftRoute** is a comprehensive, production-ready logistics operations platform designed to solve real-world last-mile delivery challenges. It enables businesses to manage zones, assign delivery agents, calculate dynamic pricing based on distance/weight, and provides customers with a live tracking timeline.

Built with performance, scalability, and modern UX in mind, the platform uses an asynchronous Python backend combined with a highly interactive, server-side rendered React frontend.

## ✨ Key Features

- **Dynamic Rate Engine**: Automated delivery cost calculations based on volumetric weight, zone distances, and order types.
- **Agent & Fleet Management**: Assign and track delivery personnel, manage availability, and handle task lifecycles (Pickup, In Transit, Delivered, Failed).
- **Interactive Live Tracking**: A responsive customer portal offering step-by-step visual timelines for package statuses.
- **Admin Dashboard**: Comprehensive CMS to manage operations, CRUD configurations for Zones & Areas, and view platform-wide analytics.
- **Role-Based Access Control (RBAC)**: Secure JWT-based authentication enforcing strict permissions across Customers, Agents, and Administrators.

## 🛠️ Tech Stack

### Frontend (User Interface)
- **Framework**: React 19 via [TanStack Start](https://tanstack.com/start) (Full-Stack React Framework)
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4 & [shadcn/ui](https://ui.shadcn.com/) for accessible, premium components
- **State & Routing**: TanStack Router and TanStack Query for seamless client-side caching and navigation
- **Deployment**: Vercel (Edge Network)

### Backend (API & Core Logic)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python)
- **Database**: PostgreSQL (hosted on Render)
- **ORM & Migrations**: SQLAlchemy (Asyncpg driver) and Alembic
- **Validation**: Pydantic v2
- **Authentication**: JWT (JSON Web Tokens) with Argon2 password hashing
- **Deployment**: Render (Infrastructure as Code via Blueprint)

---

## 🏗️ System Architecture

1. **Client-Server Separation**: The frontend and backend are completely decoupled. The frontend communicates with the backend via a strictly typed RESTful API.
2. **Asynchronous I/O**: The backend leverages `async/await` from top to bottom (FastAPI routing down to the `asyncpg` database queries) to handle high concurrency efficiently.
3. **Infrastructure as Code (IaC)**: Includes a `render.yaml` Blueprint for 1-click provisioning of the PostgreSQL database and API web service.

---

## 💻 Local Development Setup

If you'd like to run this project locally, follow the steps below:

### Prerequisites
- Node.js v18+ & npm
- Python 3.12+
- PostgreSQL (Local or Cloud instance)

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup Environment Variables (copy .env.example)
cp .env.example .env 
# -> Update DATABASE_URL and JWT_SECRET_KEY in the new .env file

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs)*

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
*Frontend will be running at [http://localhost:5173](http://localhost:5173)*

---

## 🚀 Deployment

The project is fully CI/CD ready and currently deployed across two platforms:

- **Frontend (Vercel)**: Configured as a Vercel project with the Root Directory set to `frontend/`. Environment variables ensure it correctly points to the deployed API.
- **Backend (Render)**: Automatically provisions the database and deploys the FastAPI container via the root `render.yaml` Blueprint. The deployment pipeline runs `alembic upgrade head` before booting `uvicorn`.

---

<div align="center">
  <p><i>Developed to demonstrate full-stack proficiency, API design, and modern DevOps practices.</i></p>
</div>
