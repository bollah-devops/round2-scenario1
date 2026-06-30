pipeline {
    agent any

    environment {
        PATH = "/usr/local/bin:/opt/homebrew/bin:${env.PATH}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and push Docker image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker buildx build --platform linux/amd64 \
                          -t tawa123/scenario1-platform:latest \
                          --push .
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to staging') {
            steps {
                sh '''
                    cd ansible
                    ansible-playbook -i inventory.ini playbook.yml -e "env_name=staging" --limit staging
                '''
            }
        }

        stage('Deploy to production') {
            steps {
                sh '''
                    cd ansible
                    ansible-playbook -i inventory.ini playbook.yml -e "env_name=production" --limit production
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded - deployed to staging and production"
        }
        failure {
            echo "Pipeline failed - check logs above"
        }
    }
}
