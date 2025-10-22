
pipeline {
    agent any
    stages {
        stage("Build") {
            steps {
                checkout main
                sh """
                docker compose up

                """

            }
        }
    }
}