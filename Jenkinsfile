pipeline {
    agent any

    environment {
        // Docker Hub repository and credentials ID in Jenkins
        DOCKER_IMAGE           = 'kshitij8001/student-performance-system'
        DOCKER_CREDENTIALS_ID  = 'dockerhub-credentials'
        K8S_DEPLOYMENT_NAME    = 'student-performance-app'
        IMAGE_TAG              = "${BUILD_NUMBER}"
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
        ansiColor('xterm')
    }

    stages {
        stage('Checkout Source') {
            steps {
                echo "=========================================="
                echo " Stage 1 & 2: Checking out latest code"
                echo "=========================================="
                checkout scm
                sh 'git log -1 --pretty=format:"Commit: %h by %an - %s (%ad)"'
            }
        }

        stage('Build & Test') {
            steps {
                echo "=========================================="
                echo " Stage 3: Build & Syntax / Unit Tests"
                echo "=========================================="
                sh '''
                    echo "[1/3] Verifying Python syntax..."
                    python3 -m py_compile app.py db.py reset_db.py

                    echo "[2/3] Preparing test environment..."
                    python3 -m venv test_env
                    . test_env/bin/activate
                    pip install --no-cache-dir -r requirements.txt

                    echo "[3/3] Executing automated test suite..."
                    pytest -v tests/
                    deactivate
                    rm -rf test_env
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo "=========================================="
                echo " Stage 4: Building Docker Image"
                echo "=========================================="
                sh """
                    echo "Building ${DOCKER_IMAGE}:${IMAGE_TAG} and ${DOCKER_IMAGE}:latest..."
                    docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_IMAGE}:latest .
                    docker images | grep ${DOCKER_IMAGE} || true
                """
            }
        }

        stage('Push Image') {
            steps {
                echo "=========================================="
                echo " Stage 5: Publishing Image to Registry"
                echo "=========================================="
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKER_CREDENTIALS_ID}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "Authenticating to Docker Hub as \${DOCKER_USER}..."
                        echo "\${DOCKER_PASS}" | docker login -u "\${DOCKER_USER}" --password-stdin

                        echo "Pushing ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}

                        echo "Pushing ${DOCKER_IMAGE}:latest..."
                        docker push ${DOCKER_IMAGE}:latest

                        docker logout
                    """
                }
            }
        }

        stage('Minikube Deployment') {
            steps {
                echo "=========================================="
                echo " Stage 6: Deploying Manifests to Kubernetes"
                echo "=========================================="
                sh """
                    echo "Applying ConfigMap and Secret..."
                    kubectl apply -f k8s/configmap.yaml
                    kubectl apply -f k8s/secret.yaml
                    kubectl apply -f k8s/service.yaml

                    echo "Applying Deployment with updated image tag: ${DOCKER_IMAGE}:${IMAGE_TAG}..."
                    kubectl apply -f k8s/deployment.yaml
                    kubectl set image deployment/${K8S_DEPLOYMENT_NAME} web=${DOCKER_IMAGE}:${IMAGE_TAG}
                """
            }
        }

        stage('Verification') {
            steps {
                echo "=========================================="
                echo " Stage 7: Rollout & Health Verification"
                echo "=========================================="
                sh """
                    echo "Waiting for rolling deployment to complete..."
                    kubectl rollout status deployment/${K8S_DEPLOYMENT_NAME} --timeout=120s

                    echo "=== Pods Status ==="
                    kubectl get pods -l app=student-performance-app -o wide

                    echo "=== Deployment Status ==="
                    kubectl get deployment/${K8S_DEPLOYMENT_NAME}

                    echo "=== Service Status ==="
                    kubectl get service student-performance-service

                    echo "Verifying application HTTP health endpoint in cluster..."
                    NODE_IP=\$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
                    NODE_PORT=\$(kubectl get svc student-performance-service -o jsonpath='{.spec.ports[0].nodePort}')
                    echo "App accessible at http://\${NODE_IP}:\${NODE_PORT}"
                    curl -s -f http://\${NODE_IP}:\${NODE_PORT}/health || echo "Direct curl returned non-zero (normal if minikube driver is docker without tunnel)"
                """
            }
        }
    }

    post {
        success {
            echo "========================================================="
            echo " CI/CD Pipeline Completed Successfully for Build #${BUILD_NUMBER}!"
            echo "========================================================="
        }
        failure {
            echo "========================================================="
            echo " CI/CD Pipeline Failed for Build #${BUILD_NUMBER}. Check logs above."
            echo "========================================================="
        }
        always {
            echo "Cleaning up workspace..."
            cleanWs()
        }
    }
}
