pipeline {
    agent any

    stages {

        stage('Clone') {
            steps {
                git branch: 'main',
                url: 'https://github.com/gitclixlogix/-Contentry.ai_1.000.git'
            }
        }

        stage('Install Backend') {
            steps {
                sh '''
                python3 -m venv venv
                source venv/bin/activate
                pip install -r requirements.txt
                '''
            }
        }

        stage('Install Frontend') {
            steps {
                sh '''
                cd frontend
                npm install
                npm run build
                '''
            }
        }

        stage('Restart App') {
            steps {
                sh '''
                pkill -f "gunicorn" || true
                source venv/bin/activate
                nohup gunicorn app:app --bind 0.0.0.0:8000 &
                '''
            }
        }
    }
}
