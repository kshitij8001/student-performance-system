# Student Performance System

A modernized, high-performance Flask web application for tracking departments, teachers, students, courses, enrollments, and academic performance. The backend utilizes **PostgreSQL** (hosted via [Supabase](https://supabase.com/)) with PL/pgSQL functions and triggers for automated grade averaging and audit logging.

This project features a fully automated **Cloud DevOps CI/CD Pipeline** built for **CCA 2 (TYCSE · Cloud Computing and DevOps)** deploying to **Kubernetes (Minikube)** on **AWS EC2** via **Jenkins** and **Docker Hub**.

---

## CI/CD & Cloud Deployment Overview

```
+-----------------------------------------------------------------------------------------+
|                                  CI/CD PIPELINE FLOW                                    |
|                                                                                         |
|  [GitHub Repo] ---> [Jenkins on AWS] ---> [Pytest Unit Tests] ---> [Docker Build]       |
|                                                                          |              |
|                                                                          v              |
|  [Minikube Cluster] <--- [Kubectl Deploy] <--- [Docker Hub Push] <-------+              |
|         |                                                                               |
|         +---> Rolling Update (Zero Downtime)                                            |
|         +---> 2 Replicas with Health Probes (/health)                                   |
|         +---> NodePort Service: 30080                                                   |
+-----------------------------------------------------------------------------------------+
```

### Complete CCA 2 Setup Guide
For step-by-step instructions on configuring AWS EC2, Jenkins, Docker Hub credentials, Minikube, and demonstrating the source-code change redeployment, refer to:
👉 **[CCA 2 Deployment Guide](CCA2_DEPLOYMENT_GUIDE.md)**

---

## Repository Structure

```
student-performance-system/
├── app.py                      # Flask core application & routes
├── db.py                       # PostgreSQL database connection helper
├── reset_db.py                 # Schema, triggers & seed initialization
├── Dockerfile                  # Production container definition (non-root, healthchecked)
├── .dockerignore               # Docker build exclusions
├── Jenkinsfile                 # Declarative 7-stage CI/CD pipeline
├── requirements.txt            # Python dependencies (Flask, psycopg, gunicorn, pytest)
├── CCA2_DEPLOYMENT_GUIDE.md    # Detailed AWS EC2, Jenkins, Minikube guide
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml         # 2 replicas, rolling update, probes, resource limits
│   ├── service.yaml            # NodePort service (port 30080)
│   ├── configmap.yaml          # Non-sensitive database configurations
│   └── secret.yaml             # Encrypted database credentials & secret keys
├── tests/                      # Automated test suite
│   ├── __init__.py
│   └── test_app.py             # Route gating, health endpoint & rendering tests
├── templates/                  # Jinja2 HTML templates
└── supabase/                   # SQL schemas and migration files
```

---

## Local Development & Setup

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/kshitij8001/student-performance-system.git
cd student-performance-system

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your Supabase database parameters:

```env
PGHOST=aws-1-ap-southeast-1.pooler.supabase.com
PGPORT=5432
PGUSER=postgres.<PROJECT_REF>
PGPASSWORD=your_password
PGDATABASE=postgres
PGSSLMODE=require
FLASK_SECRET_KEY=dev-secret-key-change-in-production
```

### 3. Run Automated Tests

```bash
pytest -v
```

### 4. Run the Application

```bash
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

- **Default Admin Login**: `admin` / `admin`

---

## Containerization & Kubernetes

### Build & Run Locally with Docker

```bash
# Build the Docker image
docker build -t student-performance-system:latest .

# Run the container
docker run -p 5000:5000 --env-file .env student-performance-system:latest
```

### Deploy to Kubernetes (Minikube)

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Verify deployment and service
kubectl rollout status deployment/student-performance-app
kubectl get pods,svc -l app=student-performance-app

# Access on Minikube
minikube service student-performance-service
```
