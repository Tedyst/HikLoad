pipeline {
    environment{
        imageName = 'tedyst/hikload'
        registryCredential = 'docker'
    }
    agent any
    stages {
        stage('Clone repository') {
            steps {
                checkout scm
            }
        }

        stage('Unit Testing') {
            steps {
                script {
                    sh '''
                        pip3 install -r requirements.txt
                        pytest --junitxml=text.xml
                    '''
                }
            }
        }
        
        stage('Build and Push to Docker') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'master') {
                        script {
                            image = docker.build(imageName)
                            docker.withRegistry('', registryCredential) {
                                image.push("latest")
                            }
                        }
                    }
                }
            }
        }   
    }
    post {
        always {
            junit 'text.xml'
        }
    }
}
