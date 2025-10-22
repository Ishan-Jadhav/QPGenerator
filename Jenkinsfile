
pipeline {
    agent any
    stages {
        stage("Build") {
            steps {
                checkout scm
                sh """
                docker compose up

                """

            }
        }
    }
}