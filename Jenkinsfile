pipeline {
    agent any

    environment {
        IMAGE_VERSION = "1.0.0"
        DOCKERHUB_REPO = "your-dockerhub-username"
    }

    stages {
        // STAGE 0 — Secret Scan
        // Fails pipeline if any secrets detected in repo
        stage('Secret Scan') {
            steps {
                sh '''
                echo "Running TruffleHog to scan for secrets..."
                if ! command -v trufflehog &> /dev/null; then
                    echo "Installing TruffleHog..."
                    pip install trufflehog
                fi
                trufflehog filesystem . --fail
                '''
            }
        }

        // STAGE 1 — Checkout
        stage('Checkout') {
            steps {
                checkout scm
                echo "Code checked out from GitHub"
            }
        }

        // STAGE 2 — Test
        stage('Test') {
            steps {
                echo "Running unit tests for microservices..."
                sh '''
                # Test log-generator
                cd log-generator
                pip install -r requirements.txt pytest
                pytest tests/ --tb=short -v

                # Test anomaly-detector
                cd ../anomaly-detector
                pip install -r requirements.txt pytest
                pytest tests/ --tb=short -v

                # Test dashboard
                cd ../dashboard
                pip install -r requirements.txt pytest
                pytest tests/ --tb=short -v
                '''
            }
        }

        // STAGE 3 — Build
        stage('Build Docker Images') {
            steps {
                echo "Building Docker images with version ${IMAGE_VERSION}..."
                sh '''
                docker build --build-arg VERSION=${IMAGE_VERSION} \\
                    -t ${DOCKERHUB_REPO}/log-generator:${IMAGE_VERSION} \\
                    ./log-generator

                docker build --build-arg VERSION=${IMAGE_VERSION} \\
                    -t ${DOCKERHUB_REPO}/anomaly-detector:${IMAGE_VERSION} \\
                    ./anomaly-detector

                docker build --build-arg VERSION=${IMAGE_VERSION} \\
                    -t ${DOCKERHUB_REPO}/dashboard:${IMAGE_VERSION} \\
                    ./dashboard
                '''
                echo "Docker images built successfully"
            }
        }

        // STAGE 4 — Push
        stage('Push to Docker Hub') {
            steps {
                echo "Pushing images to Docker Hub..."
                withCredentials([
                    string(credentialsId: 'DOCKERHUB_USER', variable: 'DOCKERHUB_USER'),
                    string(credentialsId: 'DOCKERHUB_PASSWORD', variable: 'DOCKERHUB_PASSWORD')
                ]) {
                    sh '''
                    # Login to Docker Hub
                    docker login -u ${DOCKERHUB_USER} -p ${DOCKERHUB_PASSWORD}

                    # Push images
                    docker push ${DOCKERHUB_REPO}/log-generator:${IMAGE_VERSION}
                    docker push ${DOCKERHUB_REPO}/anomaly-detector:${IMAGE_VERSION}
                    docker push ${DOCKERHUB_REPO}/dashboard:${IMAGE_VERSION}
                    '''
                }
                echo "Images pushed to Docker Hub"
            }
        }

        // STAGE 5 — Deploy
        stage('Deploy to Minikube') {
            steps {
                echo "Deploying to Kubernetes (Minikube)..."
                sh '''
                # Apply K8s manifests in order
                kubectl apply -f k8s/influxdb-pvc.yaml
                kubectl apply -f k8s/influxdb-deployment.yaml
                kubectl apply -f k8s/grafana-deployment.yaml
                kubectl apply -f k8s/anomaly-detector-deployment.yaml
                kubectl apply -f k8s/log-generator-deployment.yaml
                kubectl apply -f k8s/dashboard-deployment.yaml

                # Verify deployment rollouts
                kubectl rollout status deployment/log-generator
                kubectl rollout status deployment/anomaly-detector
                kubectl rollout status deployment/dashboard
                '''
                echo "Deployed to Minikube successfully"
            }
        }
    }

    post {
        always {
            echo "Pipeline complete. Build: ${IMAGE_VERSION}"
        }
        success {
            echo "✅ VPC-Stream pipeline succeeded"
        }
        failure {
            echo "❌ Pipeline failed — check logs above"
        }
    }
}
