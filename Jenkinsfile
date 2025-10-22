
pipeline {
    agent any
    stages {
        stage("Build") {
            steps {

                sh """
                checkout main
                docker compose up

                """

            }
        }
    }
}