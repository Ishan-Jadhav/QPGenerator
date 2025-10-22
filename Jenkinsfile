
pipeline {
    agent any
    stages {
        stage("Build") {
            steps {

                sh """
                git checkout main
                docker compose up

                """

            }
        }
    }
}