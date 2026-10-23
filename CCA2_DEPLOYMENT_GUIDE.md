# CCA 2: CI/CD Pipeline Implementation & Deployment Guide
**Course:** TYCSE · Cloud Computing and DevOps  
**Project:** Student Performance System  
**Repository:** [https://github.com/kshitij8001/student-performance-system](https://github.com/kshitij8001/student-performance-system)  
**Total Marks:** 10

---

## 1. Overview & Architecture

This project implements an end-to-end automated **CI/CD Pipeline** using **Jenkins**, **Docker**, **Docker Hub**, and **Kubernetes (Minikube)** deployed on an **AWS EC2** instance.

```
+--------------------------------------------------------------------------------------------------+
|                                        AWS EC2 INSTANCE                                          |
|                                                                                                  |
|   +------------+         +-------------+         +--------------+         +------------------+   |
|   |   GitHub   |  ====>  |   Jenkins   |  ====>  |  Docker Hub  |  ====>  | Kubernetes /     |   |
|   | Repository | Webhook |  Pipeline   |  Push   |   Registry   |  Pull   | Minikube Cluster |   |
|   +------------+         +-------------+         +--------------+         +------------------+   |
|                                 |                                                  |             |
|                                 v                                                  v             |
|                        Stage 1: Checkout                                   Pods (2 Replicas)     |
|                        Stage 2: Build & Test                               NodePort: 30080       |
|                        Stage 3: Docker Build                               Supabase DB           |
|                        Stage 4: Docker Push                                Zero Downtime         |
|                        Stage 5: K8s Deploy                                 Rolling Update        |
|                        Stage 6: Verification                                                     |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Pipeline Stages Explained

| Step | Stage Name | Action Performed |
|---|---|---|
| **1** | **Source Code** | Project code hosted in GitHub repository with `Dockerfile`, `Jenkinsfile`, and `k8s/`. |
| **2** | **Jenkins Checkout** | Jenkins clones the repository, checks out `main` branch, and logs the commit hash and author. |
| **3** | **Build and Test** | Python syntax is verified with `py_compile`. Dependencies installed and 5 automated unit tests executed via `pytest`. |
| **4** | **Docker Build** | Builds multi-stage, secure container image tagged as `kshitij8001/student-performance-system:${BUILD_NUMBER}` and `:latest`. |
| **5** | **Push Image** | Authenticates securely to Docker Hub using Jenkins credentials (`dockerhub-credentials`) and pushes both image tags. |
| **6** | **Minikube Deployment** | Applies `k8s/configmap.yaml`, `k8s/secret.yaml`, `k8s/service.yaml`, and rolls out updated image tag on `k8s/deployment.yaml`. |
| **7** | **Verification** | Asserts rollout completion (`kubectl rollout status`), lists running pods/services, and tests `/health` endpoint. |

---

## 3. AWS EC2 Instance Setup (Step-by-Step)

### Step 3.1: Launch EC2 Instance
1. **AMI**: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS (64-bit x86).
2. **Instance Type**: `t3.medium` or `t2.medium` (Minimum 2 vCPUs, 4 GB RAM required for Jenkins + Minikube).
3. **Storage**: At least 25 GB gp3.
4. **Security Group Inbound Rules**:
   - `Port 22` (SSH) — Your IP / Anywhere (0.0.0.0/0).
   - `Port 8080` (Jenkins Web UI) — Anywhere (0.0.0.0/0).
   - `Port 30080` (NodePort Application Service) — Anywhere (0.0.0.0/0).
   - `Port 5000` (Direct Flask/Gunicorn test, optional) — Anywhere.

---

### Step 3.2: Connect and Install Prerequisites

SSH into your EC2 instance and run the following commands:

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Java (required for Jenkins)
sudo apt install -y openjdk-17-jre-headless fontconfig curl apt-transport-https conntrack

# 3. Install Docker
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu

# 4. Install Jenkins
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins
sudo systemctl enable --now jenkins

# 5. Allow Jenkins to run Docker commands
sudo usermod -aG docker jenkins

# 6. Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 7. Install Minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm -f minikube-linux-amd64

# 8. Restart Jenkins to apply group permissions
sudo systemctl restart jenkins
```

---

### Step 3.3: Start Minikube & Configure Kubectl for Jenkins

```bash
# Start Minikube using Docker driver as ubuntu user
minikube start --driver=docker --ports=30080:30080

# Verify cluster status
kubectl get nodes

# Grant Jenkins access to the Kubernetes cluster credentials
sudo mkdir -p /var/lib/jenkins/.kube
sudo cp /home/ubuntu/.kube/config /var/lib/jenkins/.kube/config
sudo cp -r /home/ubuntu/.minikube /var/lib/jenkins/
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube
sudo chown -R jenkins:jenkins /var/lib/jenkins/.minikube

# Update minikube certificate paths inside jenkins kubeconfig
sudo sed -i 's|/home/ubuntu/|/var/lib/jenkins/|g' /var/lib/jenkins/.kube/config

# Test that Jenkins user can query kubectl
sudo -u jenkins kubectl get nodes
```

---

## 4. Configuring Jenkins

### Step 4.1: Unlock Jenkins
1. Open your browser and navigate to:
   ```
   http://<YOUR_EC2_PUBLIC_IP>:8080
   ```
2. Retrieve the initial administrator password:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
3. Paste the password, select **Install suggested plugins**, and create your admin account.

### Step 4.2: Install Required Plugins
1. Go to **Manage Jenkins** → **Plugins** → **Available plugins**.
2. Search and install:
   - **Pipeline**
   - **Docker Pipeline**
   - **AnsiColor**
3. Restart Jenkins if prompted.

### Step 4.3: Add Docker Hub Credentials
1. Go to **Manage Jenkins** → **Credentials** → **System** → **Global credentials (unrestricted)**.
2. Click **Add Credentials**:
   - **Kind**: `Username with password`
   - **Scope**: `Global`
   - **Username**: `<Your Docker Hub username>` (e.g., `kshitij8001`)
   - **Password**: `<Your Docker Hub password or Personal Access Token (PAT)>`
   - **ID**: `dockerhub-credentials` *(must match Jenkinsfile!)*
   - **Description**: `Docker Hub Credentials`
3. Click **Create**.

---

## 5. Creating the Pipeline Job

1. On Jenkins Dashboard, click **New Item**.
2. Name: `student-performance-pipeline`.
3. Type: **Pipeline** → Click **OK**.
4. In the configuration page:
   - Scroll down to **Pipeline**.
   - **Definition**: `Pipeline script from SCM`.
   - **SCM**: `Git`.
   - **Repository URL**: `https://github.com/kshitij8001/student-performance-system.git`.
   - **Branch Specifier**: `*/main`.
   - **Script Path**: `Jenkinsfile`.
5. Click **Save**.

---

## 6. Running the First Build

1. Click **Build Now** on the left menu.
2. Watch the pipeline execute through all 7 stages:
   - Checkout Source ✅
   - Build & Test (syntax check + 5 pytest tests pass) ✅
   - Docker Build (creates `${BUILD_NUMBER}` and `latest`) ✅
   - Push Image (pushes to Docker Hub) ✅
   - Minikube Deployment (applies Deployment and NodePort Service) ✅
   - Verification (`kubectl rollout status` and health assertion) ✅
3. Access the deployed app:
   ```bash
   # In your EC2 terminal:
   minikube service student-performance-service --url
   ```
   Or expose to public internet on EC2:
   ```bash
   kubectl port-forward --address 0.0.0.0 service/student-performance-service 30080:80 &
   ```
   Then open `http://<YOUR_EC2_PUBLIC_IP>:30080` in your web browser.

---

## 7. Demonstrating the Second Run (Source Code Change)

The evaluation rubric explicitly requires:
> *"After the first successful run, you must change the source code, push it, and run the pipeline again to show the new version being deployed."*

### How to execute the demo:
1. Make a visible change, for example in `templates/base.html`:
   - Change brand header or version badge from `v1.0.0` to `v1.1.0 (Live Deployment)`.
2. Commit and push from your local machine:
   ```bash
   git add templates/base.html
   git commit -m "feat(ui): update version badge to v1.1.0 for CI/CD redeployment demo"
   git push origin main
   ```
3. Go to Jenkins and click **Build Now** (or wait for GitHub webhook).
4. Point out to evaluators:
   - Build `#2` triggers automatically.
   - New Docker image tag `:2` is built and pushed to Docker Hub.
   - Kubernetes executes a **Rolling Update**: new pods spin up, readiness probes verify health, and old pods terminate with **zero downtime**.
   - Refresh `http://<YOUR_EC2_PUBLIC_IP>:30080` to reveal the updated version!

---

## 8. Viva Q&A & Evaluation Preparation

### Q1: Why do we use a declarative pipeline in Jenkinsfile?
> **Answer**: Declarative pipelines provide a structured, human-readable syntax with strict stage definitions, built-in post actions (`success`, `failure`, `always`), environment variable isolation, and clean error handling.

### Q2: Why is the container run as a non-root user in Dockerfile?
> **Answer**: In `Dockerfile`, we create `appuser` (UID 1001) with `useradd` and set `USER appuser`. Running containers as non-root mitigates container escape vulnerabilities and adheres to Kubernetes Pod Security Standards (PSS).

### Q3: What is the purpose of readinessProbe and livenessProbe in deployment.yaml?
> **Answer**:
> - `livenessProbe` checks `/health`. If the container crashes or deadlocks, Kubernetes restarts the pod.
> - `readinessProbe` ensures traffic is routed to the pod only when it is initialized and ready to serve requests. This guarantees zero-downtime rolling updates.

### Q4: Why did we choose a NodePort service on Minikube?
> **Answer**: Minikube runs inside a VM or Docker container on the host. `NodePort` exposes static port `30080` on the cluster nodes, allowing traffic to be forwarded directly from EC2 public IP to the application pods.

### Q5: How is sensitive data handled in the pipeline?
> **Answer**: Docker Hub credentials are encrypted in Jenkins' credential store and injected as environment variables using `withCredentials`. In Kubernetes, database secrets are decoupled from the image using `k8s/secret.yaml` and `k8s/configmap.yaml`.
